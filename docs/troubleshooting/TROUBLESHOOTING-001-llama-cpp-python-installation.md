# TROUBLESHOOTING-001
# llama-cpp-python Installation on Windows

Author:
Rajesh Kumar

Project:
Enterprise AI Platform

Date:
04-Aug-2026

---

## Problem

While integrating llama.cpp into the Runtime API, importing the package failed with:

ModuleNotFoundError:
No module named 'llama_cpp'

---

## Environment

OS:
Windows 11

Python:
3.13.1

Virtual Environment:
venv

Package:

llama-cpp-python

---

## Error 1

ModuleNotFoundError

Reason:

Package was installed globally but not inside the virtual environment.

Resolution:

Activated virtual environment.

Installed package inside venv.

Verified using:

pip show llama-cpp-python

---

## Error 2

pip install llama-cpp-python

Result:

Downloaded

llama_cpp_python-0.3.34.tar.gz

Installation failed.

Reason:

PyPI attempted to build the package from source.

Windows source compilation failed.

---

## Investigation

Verified:

python --version

pip --version

python -m site

python -c "import sys; print(sys.executable)"

Compatible Tags

pip debug --verbose

Observed:

Python environment was correct.

No issue with virtual environment.

Package was attempting source compilation.

---

## Root Cause

The default PyPI package downloaded the source archive.

Source compilation required C++ build steps.

The Windows build failed.

---

## Resolution

Installed the official precompiled wheel repository.

Command:

pip install llama-cpp-python \
--extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

Result:

Downloaded:

llama_cpp_python-0.3.34-py3-none-win_amd64.whl

Installation completed successfully.

---

## Validation

Verified:

pip show llama-cpp-python

Import test:

from llama_cpp import Llama

Result:

Import Successful

---

## API Validation

Started:

uvicorn app.main:app --reload

Opened:

http://127.0.0.1:8000/docs

Executed:

POST /generate

Model:

TinyLlama

Status:

200 OK

---

## Lessons Learned

✔ Difference between source package and wheel

✔ Importance of Python version compatibility

✔ Importance of Virtual Environments

✔ Understanding compatible wheel tags

✔ Official vendor wheel repositories

✔ Enterprise dependency troubleshooting

---

## References

Official llama-cpp-python repository

Official Wheel Repository

Python Packaging Documentation

## Commands Used

```bash
python --version

py -0

python -m site

pip show llama-cpp-python

python -c "from llama_cpp import Llama"

uvicorn app.main:app --reload


This is incredibly useful for future debugging.

---

## My recommendation for your repository

Since we're building this as a showcase project, I'd include **only 4–6 key screenshots per troubleshooting guide**. Too many screenshots make documentation hard to read, while a handful of well-chosen images clearly demonstrate the debugging process.

For **TROUBLESHOOTING-001**, I'd use these six screenshots:

1. ❌ `ModuleNotFoundError: No module named 'llama_cpp'`
2. 🔍 Python 3.13 virtual environment verification (`python --version` / `py -0`)
3. 🔄 Recreated virtual environment with Python 3.11
4. ✅ Successful `llama-cpp-python` installation using the wheel
5. ✅ `Import Successful!` after `from llama_cpp import Llama`
6. 🚀 Swagger UI showing the `/generate` endpoint working (your last screenshot)

Those six screenshots tell the complete story—from problem to investigation, root cause, solution, and successful validation—which is exactly the kind of documentation that leaves a strong impression in technical interviews.