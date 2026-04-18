/*
 * Página de Catálogos — gestión de listas de precios.
 *
 * Flujo de subida (dos pasos):
 *   Paso 1: el usuario arrastra/selecciona el Excel
 *           → POST /catalogs/upload → detecta columnas → muestra mapeo
 *   Paso 2: el usuario confirma/ajusta el mapeo
 *           → POST /catalogs/process → guarda productos → muestra catálogo
 *
 * El estado 'uploadStep' controla qué panel del modal mostrar.
 */

import { useState, useEffect, useRef } from 'react'
import { BookOpen, Upload, Trash2, Plus, X, Check } from 'lucide-react'
import toast from 'react-hot-toast'
import { getCatalogs, uploadExcel, processCatalog, deleteCatalog } from '../api'
import { Button, Spinner, EmptyState } from '../components/ui'
import { getErrorMessage } from '../api/client'
import type { Catalog, CatalogUploadResponse, ColumnMapping } from '../types'

/* Campos mapeables con su label legible */
const MAPPING_FIELDS: { key: keyof ColumnMapping; label: string; required: boolean }[] = [
  { key: 'name_column',           label: 'Nombre del producto',  required: true  },
  { key: 'price_column',          label: 'Precio base',          required: true  },
  { key: 'price_with_tax_column', label: 'Precio con IVA',       required: false },
  { key: 'product_code_column',   label: 'Código / clave',       required: false },
  { key: 'category_column',       label: 'Categoría',            required: false },
  { key: 'unit_column',           label: 'Unidad de venta',      required: false },
  { key: 'brand_column',          label: 'Marca',                required: false },
]

export default function CatalogsPage() {
  const [catalogs, setCatalogs]   = useState<Catalog[]>([])
  const [loading, setLoading]     = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [deleting, setDeleting]   = useState<string | null>(null)

  /* Estado del flujo de subida */
  const [uploadStep, setUploadStep]     = useState<'select' | 'mapping' | 'processing'>('select')
  const [uploadData, setUploadData]     = useState<CatalogUploadResponse | null>(null)
  const [catalogName, setCatalogName]   = useState('')
  const [mapping, setMapping]           = useState<Partial<ColumnMapping>>({})
  const [uploading, setUploading]       = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const data = await getCatalogs()
      setCatalogs(data)
    } finally {
      setLoading(false)
    }
  }

  function openModal() {
    setUploadStep('select')
    setUploadData(null)
    setCatalogName('')
    setMapping({})
    setShowModal(true)
  }

  /* Paso 1: subir el archivo */
  async function handleFileSelect(file: File) {
    setUploading(true)
    try {
      const result = await uploadExcel(file)
      setUploadData(result)
      setCatalogName(file.name.replace(/\.(xlsx|xls)$/i, ''))
      /* Pre-rellenar mapeo con las sugerencias del backend */
      setMapping(result.suggested_mapping as Partial<ColumnMapping>)
      setUploadStep('mapping')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setUploading(false)
    }
  }

  /* Paso 2: confirmar mapeo y procesar */
  async function handleProcess() {
    if (!uploadData) return
    if (!mapping.name_column || !mapping.price_column) {
      toast.error('Debes mapear al menos el nombre y el precio')
      return
    }
    if (!catalogName.trim()) {
      toast.error('El nombre del catálogo es obligatorio')
      return
    }
    setUploadStep('processing')
    try {
      const catalog = await processCatalog({
        file_key:       uploadData.file_key,
        catalog_name:   catalogName.trim(),
        column_mapping: mapping as ColumnMapping,
      })
      setCatalogs(prev => [catalog, ...prev])
      toast.success(`Catálogo creado con ${catalog.row_count.toLocaleString('es-MX')} productos`)
      setShowModal(false)
    } catch (err) {
      toast.error(getErrorMessage(err))
      setUploadStep('mapping')
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('¿Eliminar este catálogo y todos sus productos?')) return
    setDeleting(id)
    try {
      await deleteCatalog(id)
      setCatalogs(prev => prev.filter(c => c.id !== id))
      toast.success('Catálogo eliminado')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-medium text-primary">Catálogos de precios</h1>
        <Button onClick={openModal}>
          <Plus size={15} /> Subir catálogo
        </Button>
      </div>

      {/* Lista de catálogos */}
      {loading ? (
        <div className="flex justify-center py-16"><Spinner size={28} /></div>
      ) : catalogs.length === 0 ? (
        <EmptyState
          icon={<BookOpen size={32} />}
          title="Sin catálogos"
          description="Sube tu lista de precios en Excel para empezar a cotizar."
          action={<Button onClick={openModal}><Upload size={14} />Subir mi primer catálogo</Button>}
        />
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {catalogs.map(catalog => (
            <div key={catalog.id} className="card p-5 group">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-lg font-medium text-primary">{catalog.name}</p>
                  <p className="text-sm text-muted mt-0.5">
                    {catalog.row_count.toLocaleString('es-MX')} productos
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(catalog.id)}
                  disabled={deleting === catalog.id}
                  className="opacity-0 group-hover:opacity-100 text-muted hover:text-danger
                             transition-all duration-150 p-1"
                >
                  {deleting === catalog.id ? <Spinner size={14} /> : <Trash2 size={14} />}
                </button>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`badge ${catalog.source_type === 'own' ? 'badge-draft' : 'badge-sent'}`}>
                  {catalog.source_type === 'own' ? 'Lista propia' : 'Distribuidor'}
                </span>
                {catalog.distributor_name && (
                  <span className="text-xs text-muted">{catalog.distributor_name}</span>
                )}
                {catalog.margin_percentage && (
                  <span className="badge badge-accepted">+{catalog.margin_percentage}% margen</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Modal de subida ───────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 bg-primary/40 flex items-center justify-center z-50 p-4">
          <div className="bg-surface rounded-xl shadow-modal w-full max-w-lg">
            {/* Header del modal */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <h2 className="text-lg font-medium text-primary">
                {uploadStep === 'select'     ? 'Subir lista de precios'
               : uploadStep === 'mapping'   ? 'Configurar columnas'
               :                              'Procesando...'}
              </h2>
              {uploadStep !== 'processing' && (
                <button onClick={() => setShowModal(false)} className="text-muted hover:text-primary">
                  <X size={18} />
                </button>
              )}
            </div>

            <div className="p-6">
              {/* ── Paso 1: seleccionar archivo ─────────── */}
              {uploadStep === 'select' && (
                <div>
                  <p className="text-base text-muted mb-5">
                    Sube tu lista de precios en formato Excel (.xlsx o .xls).
                    Mínimo dos columnas: nombre del producto y precio.
                  </p>
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-border rounded-lg p-10
                               flex flex-col items-center gap-3 cursor-pointer
                               hover:border-primary hover:bg-bg transition-colors duration-150"
                  >
                    {uploading ? (
                      <Spinner size={28} />
                    ) : (
                      <>
                        <Upload size={28} className="text-muted" />
                        <p className="text-base font-medium text-primary">
                          Haz clic para seleccionar el archivo
                        </p>
                        <p className="text-sm text-muted">.xlsx · .xls · máx 10 MB</p>
                      </>
                    )}
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.xls"
                    className="hidden"
                    onChange={e => {
                      const file = e.target.files?.[0]
                      if (file) handleFileSelect(file)
                    }}
                  />
                </div>
              )}

              {/* ── Paso 2: mapeo de columnas ───────────── */}
              {uploadStep === 'mapping' && uploadData && (
                <div className="flex flex-col gap-4">
                  <div className="bg-bg rounded-lg px-4 py-3 text-sm text-muted">
                    Se detectaron <strong className="text-primary">{uploadData.row_count.toLocaleString('es-MX')} filas</strong> y{' '}
                    <strong className="text-primary">{uploadData.detected_columns.length} columnas</strong>.
                    Verifica que el mapeo sea correcto.
                  </div>

                  <div>
                    <label className="text-sm font-medium text-primary block mb-1">
                      Nombre del catálogo
                    </label>
                    <input
                      className="input"
                      value={catalogName}
                      onChange={e => setCatalogName(e.target.value)}
                      placeholder="Mi lista de precios"
                    />
                  </div>

                  <div className="border border-border rounded-lg divide-y divide-border">
                    {MAPPING_FIELDS.map(({ key, label, required }) => (
                      <div key={key} className="flex items-center justify-between px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <span className="text-base text-primary">{label}</span>
                          {required && (
                            <span className="text-xs text-danger font-medium">*</span>
                          )}
                          {mapping[key] && (
                            <Check size={12} className="text-success" />
                          )}
                        </div>
                        <select
                          value={mapping[key] || ''}
                          onChange={e => setMapping(p => ({
                            ...p,
                            [key]: e.target.value || null,
                          }))}
                          className="input py-1 w-48 text-sm"
                        >
                          <option value="">— No usar —</option>
                          {uploadData.detected_columns.map(col => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-3 pt-2">
                    <Button variant="secondary" onClick={() => setUploadStep('select')} className="flex-1">
                      Atrás
                    </Button>
                    <Button onClick={handleProcess} className="flex-1">
                      Crear catálogo
                    </Button>
                  </div>
                </div>
              )}

              {/* ── Paso 3: procesando ──────────────────── */}
              {uploadStep === 'processing' && (
                <div className="py-8 flex flex-col items-center gap-4">
                  <Spinner size={32} />
                  <p className="text-base text-muted">
                    Procesando {uploadData?.row_count.toLocaleString('es-MX')} productos...
                  </p>
                  <p className="text-sm text-muted">Esto puede tardar unos segundos.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
