# Deployment Log & Status Report
**Date:** December 21, 2025

## 🛠️ Work Completed

### 1. Storage Migration (C: to F:)
- **Issue:** C: drive ran out of space due to Docker images/volumes.
- **Action:** Moved Docker's WSL2 virtual disk to `F:\DockerData\docker_data.vhdx`.
- **Result:** Docker is now running from F: drive, preserving system partition space.

### 2. Local LLM Configuration (GPU Optimization)
- **Goal:** Run `dicta-il/dictalm2.0-instruct` locally on NVIDIA GTX 1080 (8GB VRAM).
- **Action:**
    - Configured **4-bit quantization** using `bitsandbytes` to reduce VRAM usage (~5GB vs 14GB+).
    - Updated `src/services/local_model.py` to use `BitsAndBytesConfig`.
    - Fixed `TypeError: Can't instantiate abstract class LocalModel` by implementing `model_name` and `system` properties.
    - **Dependency Fix:** Added `bitsandbytes` to `pyproject.toml` and `uv.lock`, then rebuilt the Docker image.
    - **Model ID Fix:** Corrected `.env` model path to `dicta-il/dictalm2.0-instruct`.

### 3. Database & Infrastructure
- **Port Conflict:** Mapped PostgreSQL to port **5433** (host) to avoid conflict with local Postgres.
- **Schema Fix:** Resolved `UndefinedTableError: relation "groupmember" does not exist` by creating and applying a new Alembic migration (`1764700002_add_group_member_table.py`).
- **Group Activation:** Manually set `managed = true` for group `120363423622261170@g.us` to enable bot responses.

### 4. Connectivity
- **Webhook:** Verified `POST /webhook` is reachable and processing messages.
- **Hugging Face:** Confirmed container can access Hugging Face Hub to download models.

---

## ⚠️ Current Status & Warnings

- **Bot Status:** 🟢 Online (Port 8000)
- **Database:** 🟢 Online (Port 5433)
- **Model Status:** 🟡 Downloading/Loading
    - **Warning:** `UserWarning: NVIDIA GeForce GTX 1080 with CUDA capability sm_61 is not compatible with the current PyTorch installation.`
    - **Impact:** The current PyTorch version targets newer GPUs (sm_70+). The model *might* fail to run on the GTX 1080, or fallback to CPU (slow).

---

## 🕵️ Investigation & Next Steps

To confirm everything is fully working, follow these steps:

### 1. Monitor Model Loading
Watch the logs to see if the model loads successfully after the download finishes (approx. 5GB).
```powershell
docker logs -f wa_llm-web-server-1
```
**Success Indicator:** Log message `Local model loaded.`
**Failure Indicator:** Crash with `CUDA error` or `capability sm_61` fatal error.

### 2. Test Inference (WhatsApp)
Once the model is loaded, send the following message in the WhatsApp group:
```text
@972559913939 summarize
```
- **Expected:** The bot should reply with a summary.
- **If Silent:** Check logs for inference errors.

### 3. Contingency Plan (If GTX 1080 Fails)
If the model crashes due to the GPU architecture warning:
- **Option A (CPU):** Disable GPU in `docker-compose.yml` (remove `deploy` section) and set `load_in_4bit=False` (will be very slow).
- **Option B (Older PyTorch):** Downgrade PyTorch in `pyproject.toml` to a version supporting Pascal (sm_61), e.g., PyTorch 2.1 or specific CUDA 11.8 builds.

### 4. Verify Data Persistence
Ensure data is actually saving to F: drive:
- Check `F:\wa_llm_data\postgres` contains data.
- Check `F:\wa_llm_data\huggingface` contains the model files.
