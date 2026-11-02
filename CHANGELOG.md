# Changelog

Semua perubahan penting pada proyek ini didokumentasikan di sini.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.1.0/),
dan proyek ini menggunakan [Semantic Versioning](https://semver.org/lang/id/).

## [Unreleased]

## [1.8.1] - 2026-11-02

### Diperbaiki
- Workflow rilis `release.yml` kini memberi izin `contents: read` di tingkat atas agar workflow
  reusable `ghcr.yml@v2` bisa start; rilis v1.8.0 gagal `startup_failure` sehingga image dan
  GitHub Release v1.8.0 tidak pernah terbit.

## [1.8.0] - 2026-11-02

### Diubah
- Workflow rilis `release.yml` dimigrasi ke caller `ghcr.yml@v2` dan kini menerbitkan image
  multi-arch `linux/amd64` + `linux/arm64` agar jalan di node SBC ARM (rujukan:
  Andhit-s-To-Do-List/shared-infra-support#23). Tag `latest` kini ikut terbit; tag `{{major}}`
  (mis. `:1`) tidak lagi dihasilkan. GitHub Release dipisah menjadi job `github-release`.

## [1.7.0] - 2026-10-22

### Ditambahkan
- Tool baca-saja `list_financial_investments(org_id)` untuk membaca daftar investasi
  keuangan (deposito, saham, reksa dana, dsb.) lewat
  `GET /organizations/{org_id}/financial-investments`.
- Tool `update_income_category` untuk mengubah `label`, `is_operational`, dan
  `sort_order` satu kategori pendapatan (partial update, admin) lewat
  `PUT /income-categories/{category_id}`.

### Diubah
- `list_income_categories` kini menyertakan `is_operational` pada tiap
  kategori pendapatan yang dikembalikan.

## [1.6.2] - 2026-06-04

### Diubah
- Migrasi infrastruktur CI ke pola Makefile + `Dockerfile.test` terpisah agar
  lingkungan test identik antara lokal dan GitHub Actions (`make test`).
- `Dockerfile` produksi tidak lagi memiliki stage `test`; image test kini
  dibangun dari `Dockerfile.test` secara terpisah.
- Workflow CI diganti dari `ci.yml` ke `test.yml` yang hanya memanggil `make test`.
- `README.md` diperbarui: dokumentasi cara menjalankan test kini mengacu ke
  `make test` / `make lint` / `make unit`.
- `.gitignore` ditambah entri `.ruff_cache/` dan `.mypy_cache/`.

### Ditambahkan
- `Makefile` dengan target standar: `build`, `lint`, `unit`, `test`, `clean`, `help`.
- `Dockerfile.test` — image khusus automated test (linter + unit) dengan strategi
  anti-artefak: source di-COPY ke image, `docker run --rm` tanpa bind-mount.
- `requirements-test.txt` — tooling test dengan versi dipin (`pytest`, `ruff`,
  `pytest-asyncio`, `respx`).
- `.dockerignore` untuk mempercepat build context Docker.

### Dihapus
- `ci.yml` (workflow lama yang menduplikasi langkah lint/unit di YAML).

## [1.6.1] - 2026-05-23

### Diperbaiki
- Format ulang `test_categories.py` sesuai Ruff agar CI lulus.

## [1.6.0] - 2026-05-23

### Ditambahkan
- Tool CRUD kategori biaya: `create_expense_category`, `update_expense_category`,
  `delete_expense_category`.

## [1.5.0] - 2026-05-20

### Ditambahkan
- Tool `reset_organization_password`.
- Tool grade-config, parent-expense-allocation, dan subsidy.

## [1.4.0] - 2026-05-15

### Diubah
- Ganti GitHub OAuth dengan Authentik sebagai identity provider.
- Perbaiki URL authorize dan token ke format Authentik 2024+.

[Unreleased]: https://github.com/andhitia-r/budget-sekolah-mcp/compare/v1.8.1...HEAD
[1.8.1]: https://github.com/andhitia-r/budget-sekolah-mcp/compare/v1.8.0...v1.8.1
[1.8.0]: https://github.com/andhitia-r/budget-sekolah-mcp/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/andhitia-r/budget-sekolah-mcp/compare/v1.6.2...v1.7.0
[1.6.2]: https://github.com/andhitia-r/budget-sekolah-mcp/compare/v1.6.1...v1.6.2
[1.6.1]: https://github.com/andhitia-r/budget-sekolah-mcp/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/andhitia-r/budget-sekolah-mcp/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/andhitia-r/budget-sekolah-mcp/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/andhitia-r/budget-sekolah-mcp/compare/v1.3.3...v1.4.0
