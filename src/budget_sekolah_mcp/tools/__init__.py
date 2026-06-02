"""
Paket tools — berisi semua tool MCP yang diekspos ke AI client.

Setiap modul di paket ini mengekspos fungsi register(mcp, client) yang
mendaftarkan tool-tool relevan ke instance FastMCP.

Modul yang tersedia:
  organizations  — CRUD organisasi (UNIT, CABANG, PUSAT)
  assumptions    — Asumsi siswa untuk UNIT
  grade_configs  — Konfigurasi jumlah & label kelas untuk UNIT
  budget_entries — Entri biaya operasional dan non-operasional
  income_entries — Entri pendapatan manual
  investments    — Investasi aset tetap baru
  depreciation   — Aset tetap lama yang masih disusutkan
  contributions  — Tarif kontribusi dan alokasi ke CABANG/PUSAT
  parent_expense_allocations — Alokasi biaya induk (CABANG/PUSAT) ke unit anak
  subsidies      — Subsidi dari CABANG/PUSAT ke organisasi penerima
  simulation     — Simulasi RAB (UP, US, income, expenses, dsb.)
  categories     — Daftar kategori biaya/pendapatan/investasi (read-only)
"""
