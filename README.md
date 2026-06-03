# budget-sekolah-mcp

MCP (Model Context Protocol) server untuk berinteraksi dengan [budget-backend-ypii](https://github.com/cantum-project/budget-backend-ypii) — backend simulasi Rencana Anggaran Belanja (RAB) Yayasan Penyelenggaraan Ilahi Indonesia (YPII).

Server ini memungkinkan AI agent (Claude Desktop, VS Code Copilot, dsb.) mengakses data dan menjalankan simulasi anggaran sekolah melalui antarmuka MCP standar.

---

## Fitur

- **Manajemen Organisasi** — buat, baca, update, hapus UNIT, CABANG, dan PUSAT
- **Asumsi Siswa** — set jumlah siswa per kelas dan jumlah staf untuk satu UNIT
- **Entri Biaya** — kelola biaya operasional (akun `5110–5250`) dan non-operasional (akun `5500–5590`)
- **Entri Pendapatan Manual** — kelola pendapatan yang tidak dihitung otomatis oleh template
- **Investasi Aset Baru** — catat pembelian aset tetap beserta depresiasi proporsional
- **Depresiasi Aset Lama** — daftarkan aset lama yang masih dalam masa penyusutan
- **Tarif Kontribusi** — set persentase kontribusi UP/US ke Pusat dan Cabang
- **Simulasi RAB** — jalankan simulasi `up`, `us`, `income`, `expenses`, `allocation`, `depreciation`, dan `summary`
- **Keamanan API Key** — lindungi endpoint HTTP/SSE dengan `MCP_API_KEY` untuk deployment cloud

---

## Tools MCP yang Tersedia

| Tool | Keterangan |
|------|-----------|
| `list_organizations` | Daftar semua organisasi |
| `get_organization` | Detail satu organisasi |
| `create_organization` | Buat organisasi baru *(admin only)* |
| `update_organization` | Update data organisasi *(admin only)* |
| `delete_organization` | Hapus organisasi *(admin only)* |
| `get_assumption` | Baca asumsi siswa satu UNIT |
| `upsert_assumption` | Set/update asumsi siswa satu UNIT |
| `list_budget_entries` | Daftar entri biaya satu organisasi |
| `create_budget_entry` | Tambah satu entri biaya |
| `bulk_create_budget_entries` | Tambah banyak entri biaya sekaligus |
| `delete_budget_entries_by_category` | Hapus semua entri biaya per kategori |
| `list_income_entries` | Daftar entri pendapatan manual |
| `create_income_entry` | Tambah satu entri pendapatan |
| `bulk_create_income_entries` | Tambah banyak entri pendapatan sekaligus |
| `list_investments` | Daftar investasi aset baru |
| `create_investment` | Tambah investasi aset baru |
| `list_depreciation` | Daftar aset lama yang disusutkan |
| `create_depreciation` | Tambah aset lama |
| `get_contribution_rates` | Baca tarif kontribusi |
| `update_contribution_rates` | Set tarif kontribusi |
| `list_expense_categories` | Daftar kategori biaya (seed data) |
| `create_expense_category` | Buat kategori biaya baru *(admin)* |
| `update_expense_category` | Ubah flag/atribut kategori biaya — mis. `is_operational` *(admin, global)* |
| `delete_expense_category` | Hapus kategori biaya *(admin)* |
| `list_income_categories` | Daftar kategori pendapatan (seed data) |
| `list_investment_categories` | Daftar kategori investasi (seed data) |
| `simulate_up` | Simulasi komponen Uang Pangkal *(UNIT only)* |
| `simulate_us` | Simulasi komponen Uang Sekolah *(UNIT only)* |
| `simulate_income` | Simulasi total pendapatan |
| `simulate_expenses` | Simulasi total biaya |
| `simulate_allocation` | Simulasi alokasi kontribusi *(CABANG/PUSAT only)* |
| `simulate_depreciation` | Simulasi penyusutan aset |
| `simulate_summary` | Ringkasan lengkap RAB |

---

## Prasyarat

- Python 3.11+
- Docker (wajib untuk menjalankan test)
- Instance [budget-backend-ypii](https://github.com/cantum-project/budget-backend-ypii) yang berjalan

---

## Instalasi & Konfigurasi

```bash
# 1. Clone repositori
git clone https://github.com/cantum-project/budget-sekolah-mcp.git
cd budget-sekolah-mcp

# 2. Salin file konfigurasi
cp .env.example .env

# 3. Edit .env sesuai instance backend yang dituju
```

Variabel konfigurasi di `.env`:

| Variabel | Wajib | Default | Keterangan |
|----------|-------|---------|-----------|
| `BUDGET_API_BASE_URL` | ✓ | — | Base URL backend, contoh: `http://api.budget-ypii-2627.local` |
| `BUDGET_API_USERNAME` | ✓ | — | Username login ke backend |
| `BUDGET_API_PASSWORD` | ✓ | — | Password login ke backend |
| `MCP_SERVER_NAME` | — | `budget-sekolah-mcp` | Nama server yang ditampilkan ke AI client |
| `MCP_LOG_LEVEL` | — | `INFO` | Level logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `HTTP_TIMEOUT` | — | `30.0` | Timeout HTTP request (detik) |
| `MCP_BASE_URL` | — | *(kosong)* | URL publik MCP server. Wajib diisi jika OAuth Authentik aktif. Contoh: `https://mcp.budget-26.cantum-ypii.com` |
| `AUTHENTIK_BASE_URL` | — | *(kosong)* | URL dasar Authentik. Contoh: `https://auth.cantum-ypii.com` |
| `AUTHENTIK_APP_SLUG` | — | *(kosong)* | Slug OAuth2 Provider di Authentik. Contoh: `budget-mcp` |
| `AUTHENTIK_CLIENT_ID` | — | *(kosong)* | Client ID dari Authentik OAuth2 Provider |
| `AUTHENTIK_CLIENT_SECRET` | — | *(kosong)* | Client Secret dari Authentik OAuth2 Provider |
| `AUTHENTIK_ALLOWED_USERNAMES` | — | *(kosong)* | `preferred_username` Authentik yang diizinkan, dipisah koma. Kosong = semua user diizinkan. |
| `MCP_API_KEY` | — | *(kosong)* | API key statis untuk VS Code / tools non-OAuth. Kosongkan untuk menonaktifkan. |

---

## Cara Menjalankan

### Mode stdio (untuk AI client)

Mode ini digunakan ketika AI client (Claude Desktop, VS Code Copilot) spawn proses server secara langsung:

```bash
# Install package
pip install -e .

# Jalankan
python -m budget_sekolah_mcp
```

### Mode SSE (untuk testing / deployment HTTP)

```bash
# Install package
pip install -e .

# Jalankan server SSE di port 9170
fastmcp run src/budget_sekolah_mcp/server.py --transport sse --port 9170
```

### Dengan Docker

```bash
# Build image production
docker build -t budget-sekolah-mcp:latest .

# Jalankan container
docker run -d --name budget-sekolah-mcp \
  -p 9170:9170 \
  -e BUDGET_API_BASE_URL=http://api.budget-ypii-2627.local \
  -e BUDGET_API_USERNAME=admin \
  -e BUDGET_API_PASSWORD=<password> \
  -e MCP_API_KEY=<api-key-opsional> \
  budget-sekolah-mcp:latest

# Verifikasi server berjalan
curl -s http://localhost:9170/sse -o /dev/null -w "Status: %{http_code}\n"

# Bersihkan container
docker stop budget-sekolah-mcp && docker rm budget-sekolah-mcp
```

---

## Integrasi dengan AI Client

### Claude Desktop

Tambahkan entri berikut ke `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "budget-sekolah": {
      "command": "python",
      "args": ["-m", "budget_sekolah_mcp"],
      "env": {
        "BUDGET_API_BASE_URL": "http://api.budget-ypii-2627.local",
        "BUDGET_API_USERNAME": "admin",
        "BUDGET_API_PASSWORD": "changeme"
      }
    }
  }
}
```

### VS Code Copilot (MCP via stdio)

Tambahkan ke `.vscode/mcp.json` atau konfigurasi workspace:

```json
{
  "servers": {
    "budget-sekolah": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "budget_sekolah_mcp"],
      "env": {
        "BUDGET_API_BASE_URL": "http://api.budget-ypii-2627.local",
        "BUDGET_API_USERNAME": "admin",
        "BUDGET_API_PASSWORD": "changeme"
      }
    }
  }
}
```

### SSE (Remote / Docker)

```json
{
  "servers": {
    "budget-sekolah": {
      "type": "sse",
      "url": "http://localhost:9170/sse",
      "headers": {
        "X-API-Key": "<MCP_API_KEY>"
      }
    }
  }
}
```

---

## Keamanan

Server mendukung dua mekanisme autentikasi yang bisa aktif bersamaan:

| Mekanisme | Digunakan oleh | Aktif jika |
|-----------|---------------|------------|
| **OAuth via Authentik** | Claude.ai, AI client berbasis browser | `AUTHENTIK_*` + `MCP_BASE_URL` dikonfigurasi |
| **API Key statis** | VS Code Copilot, tools CLI, integrasi otomatis | `MCP_API_KEY` dikonfigurasi |

### Autentikasi OAuth via Authentik (untuk Claude.ai)

Authentik digunakan sebagai identity provider (IdP). Pengguna login via Authentik; MCP server memverifikasi token menggunakan JWKS endpoint Authentik.

#### Langkah 1 — Buat OAuth2/OIDC Provider di Authentik

1. Login ke Authentik Admin (contoh: `https://auth.cantum-ypii.com`)
2. Buka **Providers → Create** → pilih **OAuth2/OpenID Connect Provider**
3. Isi konfigurasi:
   - **Name**: `budget-mcp`
   - **Client type**: `Confidential`
   - **Redirect URIs**: `https://<MCP_BASE_URL>/auth/callback`
     (contoh: `https://mcp.budget-26.cantum-ypii.com/auth/callback`)
   - **Scopes**: centang `openid`, `profile`, `email`
4. Catat **Client ID** dan **Client Secret** yang ter-generate
5. Buka **Applications → Create**
   - **Slug**: `budget-mcp`
   - **Provider**: pilih provider yang baru dibuat

#### Langkah 2 — Konfigurasi Environment Variables

Tambahkan ke `.env` (atau Docker environment):

```env
MCP_BASE_URL=https://mcp.budget-26.cantum-ypii.com
AUTHENTIK_BASE_URL=https://auth.cantum-ypii.com
AUTHENTIK_APP_SLUG=budget-mcp
AUTHENTIK_CLIENT_ID=<Client ID dari Authentik>
AUTHENTIK_CLIENT_SECRET=<Client Secret dari Authentik>
AUTHENTIK_ALLOWED_USERNAMES=
```

> **Kontrol akses sebaiknya dilakukan di Authentik** melalui **Policy Bindings** pada Application `budget-mcp` — pilih user atau group yang diizinkan. User yang tidak lolos policy Authentik akan ditolak sebelum sampai ke MCP server.
>
> `AUTHENTIK_ALLOWED_USERNAMES` adalah filter opsional tambahan di level MCP server. Kosongkan (default) jika Authentik sudah mengontrol akses dengan benar.

#### Langkah 3 — Tambahkan ke Docker Compose

```yaml
services:
  budget-mcp:
    image: ghcr.io/cakrawala-tumbuh/budget-sekolah-mcp:latest
    environment:
      BUDGET_API_BASE_URL: http://budget-api:8000
      BUDGET_API_USERNAME: admin
      BUDGET_API_PASSWORD: ${ADMIN_PASSWORD}
      MCP_BASE_URL: ${MCP_BASE_URL}
      AUTHENTIK_BASE_URL: ${AUTHENTIK_BASE_URL}
      AUTHENTIK_APP_SLUG: ${AUTHENTIK_APP_SLUG}
      AUTHENTIK_CLIENT_ID: ${AUTHENTIK_CLIENT_ID}
      AUTHENTIK_CLIENT_SECRET: ${AUTHENTIK_CLIENT_SECRET}
      AUTHENTIK_ALLOWED_USERNAMES: ${AUTHENTIK_ALLOWED_USERNAMES}
      MCP_API_KEY: ${MCP_API_KEY}
```

#### Langkah 4 — Redeploy

```bash
docker compose pull budget-mcp
docker compose up -d budget-mcp
```

---

### Autentikasi API Key (untuk VS Code / tools non-OAuth)

Lindungi endpoint SSE dengan `MCP_API_KEY`. Setiap request harus menyertakan salah satu header:

```
X-API-Key: <kunci-anda>
Authorization: Bearer <kunci-anda>
```

Generate kunci yang kuat:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

> **Catatan:** Mode stdio tidak memerlukan autentikasi — keamanannya dijamin oleh isolasi proses AI client yang me-spawn server.

---

## Menjalankan Test

> ⚠️ **Wajib menggunakan Docker.** Jangan jalankan pytest langsung via virtualenv lokal.

```bash
# Build image stage test
docker build --target test -t budget-sekolah-mcp:test .

# Jalankan semua test
docker run --rm budget-sekolah-mcp:test

# Jalankan satu file test
docker run --rm budget-sekolah-mcp:test python -m pytest tests/test_simulation.py -v

# Jalankan satu test case
docker run --rm budget-sekolah-mcp:test python -m pytest tests/test_simulation.py::TestSimulationTools::test_simulate_up -v
```

---

## CI/CD

| Workflow | Trigger | Aksi |
|----------|---------|------|
| `ci.yml` | Push/PR ke `master` | Lint (Ruff) + Build Docker + Unit test |
| `release.yml` | Push tag `v*.*.*` | Build & push image ke GHCR + GitHub Release otomatis |

Image tersedia di:
```
ghcr.io/cantum-project/budget-sekolah-mcp:<tag>
```

---

## Struktur Direktori

```
budget-sekolah-mcp/
├── src/
│   └── budget_sekolah_mcp/
│       ├── server.py        # Entry point FastMCP
│       ├── config.py        # Konfigurasi via pydantic-settings
│       ├── client.py        # Async HTTP client (httpx)
│       ├── auth.py          # Manajemen JWT (login, refresh)
│       ├── asgi.py          # ASGI app untuk transport HTTP/SSE
│       ├── middleware.py    # ApiKeyMiddleware untuk keamanan SSE
│       └── tools/           # Implementasi setiap tool MCP
├── tests/                   # Unit test (pytest + respx)
├── .github/
│   └── workflows/           # GitHub Actions CI/CD
├── Dockerfile               # Multi-stage: base, test, production
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Stack Teknologi

| Komponen | Library |
|----------|---------|
| MCP Framework | [FastMCP](https://github.com/jlowin/fastmcp) ≥ 2.0 |
| HTTP Client | httpx (async) |
| Validasi & Config | pydantic-settings v2 |
| Testing | pytest + pytest-asyncio + respx |
| Linting | Ruff |
| Runtime | Python 3.11+ |
