import logging
import os
import time

import requests

logger = logging.getLogger(__name__)


class GPULifecycleError(RuntimeError):
    pass


class GPULifecycleService:
    """
    Controls which GPU inference backend owns the single Tesla T4.

    Supported backends:
      tinyllama
      phi3

    Only one backend should be active at a time.
    """

    NAMESPACE = os.getenv("K8S_NAMESPACE", "default")

    TINYLLAMA_DEPLOYMENT = os.getenv(
        "TINYLLAMA_DEPLOYMENT",
        "tinyllama",
    )

    VLLM_DEPLOYMENT = os.getenv(
        "VLLM_DEPLOYMENT",
        "vllm",
    )

    READY_TIMEOUT = int(
        os.getenv("MODEL_READY_TIMEOUT", "300")
    )

    POLL_INTERVAL = int(
        os.getenv("MODEL_READY_POLL_INTERVAL", "5")
    )

    def __init__(self):
        self.host = os.getenv("KUBERNETES_SERVICE_HOST")
        self.port = os.getenv(
            "KUBERNETES_SERVICE_PORT",
            "443",
        )

        if not self.host:
            raise RuntimeError(
                "KUBERNETES_SERVICE_HOST is not available"
            )

        self.base_url = (
            f"https://{self.host}:{self.port}"
        )

        token_path = (
            "/var/run/secrets/kubernetes.io/serviceaccount/token"
        )
        ca_path = (
            "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        )

        if not os.path.isfile(token_path):
            raise RuntimeError(
                "Kubernetes service-account token not mounted"
            )

        with open(
            token_path,
            "r",
            encoding="utf-8",
        ) as fh:
            token = fh.read().strip()

        self.ca_path = ca_path

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/merge-patch+json",
            }
        )

        self.deployment_url_base = (
            f"{self.base_url}"
            f"/apis/apps/v1/namespaces/{self.NAMESPACE}"
            f"/deployments"
        )

        self.current_model = None

        logger.info(
            "GPU lifecycle manager initialized: namespace=%s",
            self.NAMESPACE,
        )

    def _deployment_url(self, name: str) -> str:
        return f"{self.deployment_url_base}/{name}"

    def _scale_url(self, name: str) -> str:
        return f"{self._deployment_url(name)}/scale"

    def _get_deployment(self, name: str) -> dict:
        response = self.session.get(
            self._deployment_url(name),
            verify=self.ca_path,
            timeout=10,
        )

        if not response.ok:
            raise GPULifecycleError(
                f"Failed to get deployment {name}: "
                f"{response.status_code} {response.text}"
            )

        return response.json()

    def _scale(self, name: str, replicas: int) -> None:
        logger.info(
            "Scaling deployment %s -> %s",
            name,
            replicas,
        )

        response = self.session.patch(
            self._scale_url(name),
            json={"spec": {"replicas": replicas}},
            verify=self.ca_path,
            timeout=15,
        )

        if not response.ok:
            raise GPULifecycleError(
                f"Failed to scale {name} to {replicas}: "
                f"{response.status_code} {response.text}"
            )

    def _wait_for_replicas(
        self,
        name: str,
        desired: int,
    ) -> None:
        deadline = time.monotonic() + self.READY_TIMEOUT

        while time.monotonic() < deadline:
            deployment = self._get_deployment(name)

            spec = deployment.get("spec", {})
            status = deployment.get("status", {})

            replicas = spec.get("replicas", 0)
            ready = status.get("readyReplicas", 0)
            available = status.get("availableReplicas", 0)

            logger.info(
                "Deployment=%s desired=%s replicas=%s ready=%s available=%s",
                name,
                desired,
                replicas,
                ready,
                available,
            )

            if desired == 0:
                if replicas == 0:
                    return
            else:
                if (
                    replicas == desired
                    and ready >= desired
                    and available >= desired
                ):
                    return

            time.sleep(self.POLL_INTERVAL)

        raise GPULifecycleError(
            f"Timed out waiting for deployment "
            f"{name} to reach replicas={desired}"
        )

    def get_active_model(self):
        """
        Determine actual active backend from Kubernetes.

        Returns:
          tinyllama
          phi3
          None
        """
        tiny = self._get_deployment(
            self.TINYLLAMA_DEPLOYMENT
        )
        vllm = self._get_deployment(
            self.VLLM_DEPLOYMENT
        )

        tiny_replicas = (
            tiny.get("spec", {}).get("replicas", 0)
        )
        vllm_replicas = (
            vllm.get("spec", {}).get("replicas", 0)
        )

        if tiny_replicas > 0 and vllm_replicas == 0:
            return "tinyllama"

        if vllm_replicas > 0 and tiny_replicas == 0:
            return "phi3"

        if tiny_replicas == 0 and vllm_replicas == 0:
            return None

        raise GPULifecycleError(
            "Invalid GPU state: both TinyLlama and vLLM "
            "are active"
        )

    def activate(self, model: str) -> None:
        model = model.lower().strip()

        if model not in {"tinyllama", "phi3"}:
            raise GPULifecycleError(
                f"Unsupported GPU model: {model}"
            )

        active = (
            self.TINYLLAMA_DEPLOYMENT
            if model == "tinyllama"
            else self.VLLM_DEPLOYMENT
        )

        inactive = (
            self.VLLM_DEPLOYMENT
            if model == "tinyllama"
            else self.TINYLLAMA_DEPLOYMENT
        )

        actual_model = self.get_active_model()

        logger.info(
            "Requested GPU model=%s actual_active_model=%s",
            model,
            actual_model,
        )

        if actual_model == model:
            self.current_model = model
            logger.info(
                "GPU backend already active: %s",
                model,
            )
            return

        # Always release the current GPU backend first.
        self._scale(inactive, 0)
        self._wait_for_replicas(inactive, 0)

        # Then start the requested backend.
        self._scale(active, 1)
        self._wait_for_replicas(active, 1)

        self.current_model = model

        logger.info(
            "GPU backend activated successfully: %s",
            model,
        )


gpu_lifecycle_service = GPULifecycleService()
