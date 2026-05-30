# Copilot Instructions — budget-sekolah-mcp

> **PENTING:** Instruksi ini bersifat **wajib** dan harus dipatuhi sepenuhnya pada setiap sesi kerja.
> Sebelum memulai tugas apapun, baca ulang checklist di bawah ini dan pastikan setiap poin dipenuhi.

---

## Checklist Wajib Sebelum Menulis Kode Baru

Jalankan checklist ini setiap kali akan membuat atau menambahkan kode:

- [ ] Sudah membaca bagian instruksi yang relevan di dokumen ini
- [ ] Struktur direktori sesuai dengan yang ditetapkan di bagian **Struktur Direktori**
- [ ] Setiap file Python baru memiliki **docstring modul** (Google-style)
- [ ] Setiap fungsi/tool baru memiliki **docstring fungsi** (Google-style) dengan `Args`, `Returns`, `Raises`, `Example`
- [ ] Port yang digunakan adalah **9170** (bukan port standar)
- [ ] URL endpoint di-hard-code hanya di `client.py`, **tidak** di tempat lain
- [ ] Credential dan token **tidak** disimpan ke disk atau log

---

## Checklist Wajib Sebelum Commit

Jalankan checklist ini setiap kali akan melakukan commit:

- [ ] Semua docstring yang terpengaruh perubahan sudah **diperbarui**
- [ ] Unit test untuk kode yang diubah sudah **diperbarui atau ditambahkan**
- [ ] Image Docker stage `test` berhasil di-build: `docker build --target test -t budget-sekolah-mcp:test .`
- [ ] Seluruh test suite **lulus** di Docker: `docker run --rm budget-sekolah-mcp:test`
- [ ] Commit message menggunakan **bahasa Indonesia** dan informatif
- [ ] **TIDAK ADA** test yang gagal — commit dilarang jika ada test merah

---

## Checklist Wajib Sebelum Push / Interaksi GitHub

- [ ] Semua checklist pre-commit di atas sudah terpenuhi
- [ ] Sudah menunggu instruksi eksplisit dari user: push ke `master` langsung **atau** buat PR?
- [ ] Jika tidak ada instruksi eksplisit → **tanyakan dulu**, jangan push sendiri
- [ ] Semua interaksi GitHub (PR, release, dsb.) menggunakan **GitHub CLI (`gh`)**, bukan web manual

---

## Checklist Wajib Saat Merevisi Kode

- [ ] Docstring fungsi/modul yang direvisi sudah **diperbarui** mencerminkan perilaku baru
- [ ] Test yang sudah ada sudah **disesuaikan** dengan perilaku baru
- [ ] Test case baru sudah **ditambahkan** untuk logika baru
- [ ] Image Docker stage `test` berhasil di-build ulang
- [ ] Seluruh test suite **lulus** di Docker setelah revisi

---

## Tujuan Proyek

Proyek ini adalah **MCP (Model Context Protocol) server** untuk berinteraksi dengan API backend simulasi anggaran sekolah YPII (`budget-backend-ypii`). Server ini memungkinkan AI agent (Claude, Copilot, dsb.) untuk mengakses data dan menjalankan simulasi anggaran melalui antarmuka MCP standar.

Dibangun di atas **FastMCP** — framework Python untuk membangun MCP server secara cepat dan terstruktur.

---

## Stack Teknologi

| Komponen | Library / Versi |
|----------|----------------|
| MCP Framework | fastmcp ≥ 2.0 |
| HTTP Client | httpx (async) |
| Validasi & Config | pydantic-settings v2 |
| Testing | pytest + pytest-asyncio + respx |
| Linting | Ruff |
| Runtime | Python 3.11+ |

**Python minimum: 3.11+** (pakai sintaks `X | Y` untuk union type)

---

## Struktur Direktori

```
budget-sekolah-mcp/
├── .github/
│   ├── copilot-instructions.md
│   └── workflows/
│       ├── ci.yml          # Lint + unit test (push/PR ke master)
│       └── release.yml     # GitHub Release + push image ke GHCR (pada tagging)
├── src/
│   └── budget_sekolah_mcp/
│       ├── __init__.py
│       ├── server.py       # Entry point — instansiasi FastMCP dan registrasi semua tool
│       ├── config.py       # Settings via pydantic-settings (baca dari .env)
│       ├── client.py       # Async HTTP client wrapper (httpx) untuk budget API
│       ├── auth.py         # Manajemen autentikasi JWT (login, refresh, header)
│       └── tools/
│           ├── __init__.py
│           ├── organizations.py   # Tool: list/get/create/update/delete organisasi
│           ├── assumptions.py     # Tool: get/upsert asumsi siswa (UNIT)
│           ├── budget_entries.py  # Tool: CRUD entri biaya operasional & non-op
│           ├── income_entries.py  # Tool: CRUD entri pendapatan manual
│           ├── investments.py     # Tool: CRUD investasi aset baru
│           ├── depreciation.py    # Tool: CRUD aset lama (depresiasi)
│           ├── contributions.py   # Tool: set tarif kontribusi & alokasi
│           ├── simulation.py      # Tool: jalankan simulasi (up, us, income, expenses, dsb.)
│           └── categories.py      # Tool: baca kategori biaya/pendapatan/investasi (read-only)
├── tests/
│   ├── conftest.py         # Fixtures: mock client, server instance
│   ├── test_organizations.py
│   ├── test_assumptions.py
│   ├── test_budget_entries.py
│   ├── test_income_entries.py
│   ├── test_investments.py
│   ├── test_depreciation.py
│   ├── test_contributions.py
│   ├── test_simulation.py
│   └── test_categories.py
├── .env.example
├── .gitignore
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## Konsep Domain (diambil dari budget-backend-ypii)

### Hierarki Organisasi

| `org_type` | Keterangan |
|------------|-----------|
| `UNIT` | Satuan pendidikan (sekolah, TK, daycare, dll.) |
| `CABANG` | Cabang YPII — mengelola beberapa UNIT |
| `PUSAT` | Kantor pusat YPII |

### Simulasi yang Tersedia

| Tipe Simulasi | Endpoint Backend | Hanya Untuk |
|---------------|-----------------|-------------|
| `up` | `/simulation/up` | UNIT |
| `us` | `/simulation/us` | UNIT |
| `income` | `/simulation/income` | semua |
| `expenses` | `/simulation/expenses` | semua |
| `allocation` | `/simulation/allocation` | CABANG, PUSAT |
| `depreciation` | `/simulation/depreciation` | semua |
| `summary` | `/simulation/summary` | semua |

---

## Konfigurasi (`.env`)

| Variabel | Default | Keterangan |
|----------|---------|-----------|
| `BUDGET_API_BASE_URL` | — | **Wajib** — Base URL backend, contoh: `http://api.budget-ypii-2627.local` |
| `BUDGET_API_USERNAME` | — | **Wajib** — Username untuk login ke backend |
| `BUDGET_API_PASSWORD` | — | **Wajib** — Password untuk login ke backend |
| `MCP_SERVER_NAME` | `budget-sekolah-mcp` | Nama server MCP yang ditampilkan ke client |
| `MCP_LOG_LEVEL` | `INFO` | Level logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `HTTP_TIMEOUT` | `30.0` | Timeout HTTP request (detik) |

---

## Cara Menjalankan (Development)

```bash
# Salin dan sesuaikan konfigurasi
cp .env.example .env

# Install dependencies (development)
pip install -e ".[dev]"

# Jalankan MCP server (stdio transport — untuk digunakan oleh AI client)
python -m budget_sekolah_mcp

# Atau dengan uvicorn (SSE transport — untuk testing via browser/curl)
fastmcp run src/budget_sekolah_mcp/server.py --transport sse --port 9170
```

**Port tidak standar yang digunakan: `9170`** (SSE transport, untuk testing lokal)

---

## Cara Menjalankan dengan Docker (Wajib untuk Test Lokal)

> ⚠️ **WAJIB dan TIDAK DAPAT DINEGOSIASIKAN: semua pengujian lokal harus menggunakan Docker.**
> Menjalankan pytest langsung via virtualenv lokal adalah **PELANGGARAN** instruksi ini.

```bash
# Build image lokal (stage test)
docker build --target test -t budget-sekolah-mcp:test .

# Jalankan semua unit test
docker run --rm budget-sekolah-mcp:test

# Jalankan satu file test
docker run --rm budget-sekolah-mcp:test python -m pytest tests/test_simulation.py -v

# Jalankan satu test case
docker run --rm budget-sekolah-mcp:test python -m pytest tests/test_simulation.py::TestSimulationTools::test_simulate_up -v

# Build image production
docker build -t budget-sekolah-mcp:latest .

# Jalankan server SSE di port 9170 (port tidak standar)
docker run -d --name budget-sekolah-mcp-test \
  -p 9170:9170 \
  -e BUDGET_API_BASE_URL=http://api.budget-ypii-2627.local \
  -e BUDGET_API_USERNAME=admin \
  -e BUDGET_API_PASSWORD=<password> \
  budget-sekolah-mcp:latest

# Verifikasi server berjalan
curl -s http://localhost:9170/sse -o /dev/null -w "Status: %{http_code}\n"

# Bersihkan container
docker stop budget-sekolah-mcp-test && docker rm budget-sekolah-mcp-test
```

---

## Desain Dockerfile (Multi-stage)

```
Stage: base      → python:3.11-slim, install runtime dependencies
Stage: test      → base + install dev dependencies + copy tests + CMD pytest
Stage: production → base + copy src + CMD fastmcp run ... --transport sse --port 9170
```

Image production **tidak** menyertakan test files dan dev dependencies.

---

## Desain Tool MCP

Setiap tool diimplementasikan sebagai fungsi async Python yang didekorasi dengan `@mcp.tool()`. Gunakan docstring Google-style sebagai deskripsi tool untuk AI client.

### Konvensi Penamaan Tool

| Pola | Contoh |
|------|--------|
| `list_<resource>` | `list_organizations` |
| `get_<resource>` | `get_organization` |
| `create_<resource>` | `create_organization` |
| `update_<resource>` | `update_organization` |
| `delete_<resource>` | `delete_organization` |
| `simulate_<type>` | `simulate_up`, `simulate_summary` |

### Penanganan Error di Tool

Tool mengembalikan pesan error terstruktur (bukan raise exception) agar AI client dapat memproses hasilnya dengan baik:

```python
# Contoh pola return error
if response.status_code == 404:
    return {"error": "Organization not found", "org_id": org_id}
```

---

## GitHub Actions

### `ci.yml` — Lint + Unit Test

- **Trigger:** `push` ke `master` dan `pull_request` ke `master`
- **Steps:**
  1. Checkout kode
  2. Setup Python 3.11
  3. Install Ruff
  4. Jalankan `ruff check .` dan `ruff format --check .`
  5. Build Docker image stage `test`
  6. Jalankan `docker run --rm budget-sekolah-mcp:test`

### `release.yml` — GitHub Release + GHCR Image

- **Trigger:** `push` tag yang cocok dengan pola `v*.*.*` di branch `master`
- **Steps:**
  1. Checkout kode
  2. Login ke GHCR (`ghcr.io`) menggunakan `GITHUB_TOKEN`
  3. Extract metadata (tag, label) untuk Docker image
  4. Build dan push image ke `ghcr.io/<owner>/budget-sekolah-mcp:<tag>`
  5. Buat GitHub Release otomatis dengan changelog dari commit messages

---

## Autentikasi ke Backend API

MCP server login ke backend satu kali saat startup, menyimpan JWT token di memori, dan me-refresh token jika expired (HTTP 401). Tidak ada state yang disimpan ke disk.

Alur autentikasi:

```
startup
  → POST /auth/login (username + password dari .env)
  → simpan access_token di memori
  → setiap request HTTP: header Authorization: Bearer <token>
  → jika response 401 → re-login → retry request sekali
```

---

## Panduan Pengembangan

### Menambah Tool Baru
1. Buat/edit file di `src/budget_sekolah_mcp/tools/`
2. Tambahkan fungsi async dengan dekorator `@mcp.tool()`
3. Registrasikan di `server.py` jika belum di-include secara otomatis
4. **Wajib:** tulis docstring modul dan docstring fungsi sebelum kode di-commit
5. **Wajib:** tambahkan test di `tests/` dan pastikan lulus di Docker

### Larangan Mutlak

Larangan berikut bersifat **tidak dapat dilanggar** dalam kondisi apapun:

| Larangan | Alasan |
|----------|--------|
| Simpan credential/token ke disk atau log | Risiko keamanan — token API tidak boleh persisten |
| Hard-code URL endpoint di luar `client.py` | Melanggar single-source-of-truth untuk konfigurasi |
| Jalankan test di luar Docker | Konsistensi environment wajib dijaga |
| Modifikasi image GHCR secara manual | Semua rilis harus traceable via GitHub Action |

---

## Konvensi Docstring

> **WAJIB:** Setiap fungsi, class, dan modul **harus** memiliki docstring informatif menggunakan format **Google-style**.
> Kode tanpa docstring **tidak boleh** di-commit.

Docstring yang informatif adalah kunci agar kode dapat dibaca ulang dengan cepat tanpa perlu menelusuri implementasi satu per satu.

### Format Docstring Fungsi/Tool

```python
async def simulate_up(org_id: int) -> dict:
    """Jalankan simulasi komponen Uang Pangkal (UP) untuk satu organisasi UNIT.

    Memanggil GET /organizations/{org_id}/simulation/up pada backend API.
    Hanya berlaku untuk organisasi bertipe UNIT. Mengembalikan rincian
    komponen biaya yang membentuk tarif UP beserta total dan tarif per siswa baru.

    Args:
        org_id: ID numerik organisasi UNIT yang akan disimulasikan.

    Returns:
        Dict berisi hasil simulasi UP, termasuk kunci:
        - ``components``: daftar item biaya komponen UP
        - ``total``: total biaya UP (Rp)
        - ``rate_per_student``: tarif UP per siswa baru (Rp)

    Raises:
        Tidak me-raise exception. Jika terjadi error, kembalikan dict dengan
        kunci ``error`` berisi pesan error dan ``org_id`` sebagai konteks.

    Example:
        >>> result = await simulate_up(org_id=3)
        >>> result["rate_per_student"]
        5000000
    """
```

### Format Docstring Modul

Setiap file Python dimulai dengan docstring modul yang menjelaskan:
- Tujuan modul
- Daftar tool/fungsi utama yang tersedia
- Dependensi modul lain yang digunakan

```python
"""
Tool MCP untuk simulasi anggaran organisasi.

Menyediakan tool-tool untuk menjalankan berbagai tipe simulasi RAB
terhadap organisasi di budget-backend-ypii.

Tools yang tersedia:
  simulate_up          — Simulasi komponen Uang Pangkal (UNIT only)
  simulate_us          — Simulasi komponen Uang Sekolah (UNIT only)
  simulate_income      — Simulasi total pendapatan
  simulate_expenses    — Simulasi total biaya
  simulate_allocation  — Simulasi alokasi kontribusi (CABANG/PUSAT only)
  simulate_depreciation — Simulasi penyusutan aset
  simulate_summary     — Ringkasan lengkap RAB

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""
```

---

## Wajib Dilakukan Saat Merevisi Kode

> **PERINGATAN:** Melewati salah satu langkah di bawah ini adalah **pelanggaran** instruksi ini.
> Semua langkah berikut **harus** diselesaikan secara bersamaan — tidak boleh dilakukan sebagian.

### 1. Revisi Docstring
- Perbarui docstring fungsi/class/modul yang diubah agar mencerminkan perilaku terbaru
- Jika ada parameter baru, tambahkan di bagian `Args`
- Jika return value berubah, perbarui bagian `Returns`
- Jika fungsi baru ditambahkan, docstring wajib ada sebelum kode di-commit

### 2. Revisi dan Jalankan Ulang Unit Test
- Perbarui test yang sudah ada jika perilaku fungsi berubah
- Tambahkan test case baru untuk logika baru yang ditambahkan
- **Jalankan ulang seluruh test suite via Docker** setelah setiap perubahan:

```bash
# Build ulang image test (wajib setelah perubahan kode)
docker build --target test -t budget-sekolah-mcp:test .

# Jalankan seluruh test
docker run --rm budget-sekolah-mcp:test

# Pastikan semua test lulus sebelum commit
```

- **DILARANG KERAS** commit jika ada test yang gagal
- **DILARANG KERAS** menjalankan test dengan `pytest` lokal tanpa Docker
- Jika build Docker gagal, **perbaiki dulu** sebelum melanjutkan — jangan diabaikan

---

## Konvensi Git Commit

Gunakan bahasa Indonesia. Commit message informatif:

```
Tambah tool simulate_up dan simulate_us untuk simulasi tarif

Implementasi di tools/simulation.py menggunakan httpx async client.
Tool memanggil GET /organizations/{id}/simulation/up dan /us.
Menambah test case di tests/test_simulation.py.
```

---

## Konvensi Tag (Semantic Versioning)

Format: **`vMAJOR.MINOR.PATCH`**

| Jenis Perubahan | Bump |
|----------------|------|
| Bug fix, perbaikan kecil | **Patch** |
| Tool baru, fitur baru non-breaking | **Minor** |
| Breaking: ubah interface tool, hapus tool | **Major** |

```bash
# Cek tag terakhir
git tag --sort=-v:refname | head -5

# Buat annotated tag
git tag -a v1.0.0 -m "Rilis pertama budget-sekolah-mcp"

# Push tag ke remote
git push origin v1.0.0
```

---

## Konvensi Push ke GitHub

> **WAJIB:** Selalu tunggu instruksi eksplisit dari user sebelum push atau membuat PR.
> **DILARANG** mengambil keputusan push secara mandiri.

- **Ikuti instruksi eksplisit** dari user: push langsung ke `master` atau buat Pull Request (PR)
- Jika tidak ada instruksi eksplisit → **tanyakan dulu**, jangan bertindak sendiri
- **Wajib** menggunakan **GitHub CLI (`gh`)** untuk semua interaksi GitHub (buat PR, release, dsb.) — bukan melalui web atau API manual

```bash
# Push langsung ke master
git push origin master

# Buat PR
git push origin <nama-branch>
gh pr create --title "Judul PR" --body "Deskripsi perubahan"
```
