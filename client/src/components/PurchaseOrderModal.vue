<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ mode === 'create' ? 'Create Purchase Order' : 'Purchase Order Details' }}</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="shortage-header">
              <div class="shortage-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <rect x="12" y="6" width="24" height="36" rx="2" stroke="currentColor" stroke-width="3"/>
                  <path d="M18 16H30M18 24H30M18 32H26" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="shortage-title-section">
                <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <span class="priority-badge" :class="backlogItem.priority">
                {{ backlogItem.priority }} Priority
              </span>
            </div>

            <!-- Create mode: raise a new PO against the shortage -->
            <template v-if="mode === 'create'">
              <div class="shortage-summary">
                <div class="summary-card danger">
                  <div class="summary-label">Shortage Amount</div>
                  <div class="summary-value">{{ shortage }} units</div>
                </div>
                <div class="summary-card warning">
                  <div class="summary-label">Days Delayed</div>
                  <div class="summary-value">{{ backlogItem.days_delayed }} days</div>
                </div>
              </div>

              <div v-if="submitError" class="form-error-banner">{{ submitError }}</div>

              <form class="po-form" @submit.prevent="submit">
                <div class="form-group">
                  <label class="form-label" for="po-supplier">Supplier Name *</label>
                  <input
                    id="po-supplier"
                    v-model="form.supplier_name"
                    type="text"
                    class="form-input"
                    :class="{ invalid: errors.supplier_name }"
                    placeholder="e.g. Acme Components Ltd."
                  />
                  <span v-if="errors.supplier_name" class="field-error">{{ errors.supplier_name }}</span>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label" for="po-quantity">Quantity *</label>
                    <input
                      id="po-quantity"
                      v-model.number="form.quantity"
                      type="number"
                      min="1"
                      class="form-input"
                      :class="{ invalid: errors.quantity }"
                    />
                    <span v-if="errors.quantity" class="field-error">{{ errors.quantity }}</span>
                  </div>

                  <div class="form-group">
                    <label class="form-label" for="po-unit-cost">Unit Cost (USD) *</label>
                    <input
                      id="po-unit-cost"
                      v-model.number="form.unit_cost"
                      type="number"
                      min="0"
                      step="0.01"
                      class="form-input"
                      :class="{ invalid: errors.unit_cost }"
                      placeholder="0.00"
                    />
                    <span v-if="errors.unit_cost" class="field-error">{{ errors.unit_cost }}</span>
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label" for="po-delivery-date">Expected Delivery Date *</label>
                  <input
                    id="po-delivery-date"
                    v-model="form.expected_delivery_date"
                    type="date"
                    class="form-input"
                    :class="{ invalid: errors.expected_delivery_date }"
                  />
                  <span v-if="errors.expected_delivery_date" class="field-error">{{ errors.expected_delivery_date }}</span>
                </div>

                <div class="form-group">
                  <label class="form-label" for="po-notes">Notes</label>
                  <textarea
                    id="po-notes"
                    v-model="form.notes"
                    class="form-textarea"
                    rows="3"
                    placeholder="Optional notes for this purchase order"
                  ></textarea>
                </div>

                <div v-if="estimatedTotal > 0" class="estimated-total">
                  <!-- A PO total is a precise committed spend amount, not a dashboard
                       aggregate, so it needs cents (e.g. 10 x $9.99 = $99.90, not $100). -->
                  Estimated Total: <strong>{{ formatCurrencyWithDecimals(estimatedTotal, currentCurrency, 2) }}</strong>
                </div>
              </form>
            </template>

            <!-- View mode: read-only summary of an existing PO -->
            <template v-else>
              <div v-if="backlogItem.purchase_order">
                <div class="shortage-summary">
                  <div class="summary-card info">
                    <div class="summary-label">Total Cost</div>
                    <!-- Same reasoning as Estimated Total above: this is a committed PO
                         spend figure, not a dashboard aggregate, so it needs cents. -->
                    <div class="summary-value">{{ formatCurrencyWithDecimals(totalCost, currentCurrency, 2) }}</div>
                  </div>
                  <div class="summary-card neutral">
                    <div class="summary-label">Status</div>
                    <div class="summary-value">
                      <span class="badge" :class="statusBadgeClass">{{ backlogItem.purchase_order.status }}</span>
                    </div>
                  </div>
                </div>

                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">PO ID</div>
                    <div class="info-value order-id">{{ backlogItem.purchase_order.id }}</div>
                  </div>

                  <div class="info-item">
                    <div class="info-label">Supplier</div>
                    <div class="info-value">{{ backlogItem.purchase_order.supplier_name }}</div>
                  </div>

                  <div class="info-item">
                    <div class="info-label">Quantity</div>
                    <div class="info-value">{{ backlogItem.purchase_order.quantity }} units</div>
                  </div>

                  <div class="info-item">
                    <div class="info-label">Unit Cost</div>
                    <!-- Per-unit price needs decimal precision (e.g. $12.50) — formatCurrency
                         rounds to whole units, which is correct for aggregate figures elsewhere
                         but misleading here. -->
                    <div class="info-value">{{ formatCurrencyWithDecimals(backlogItem.purchase_order.unit_cost, currentCurrency, 2) }}</div>
                  </div>

                  <div class="info-item">
                    <div class="info-label">Expected Delivery</div>
                    <div class="info-value">{{ formatDate(backlogItem.purchase_order.expected_delivery_date) }}</div>
                  </div>

                  <div class="info-item">
                    <div class="info-label">Created</div>
                    <div class="info-value">{{ formatDate(backlogItem.purchase_order.created_date) }}</div>
                  </div>

                  <div v-if="backlogItem.purchase_order.notes" class="info-item notes-item">
                    <div class="info-label">Notes</div>
                    <div class="info-value">{{ backlogItem.purchase_order.notes }}</div>
                  </div>
                </div>
              </div>
              <div v-else class="no-po-data">
                No purchase order details are available for this item.
              </div>
            </template>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">{{ mode === 'create' ? 'Cancel' : 'Close' }}</button>
            <button
              v-if="mode === 'create'"
              type="button"
              class="btn-primary"
              :disabled="submitting"
              @click="submit"
            >
              {{ submitting ? 'Creating...' : 'Create Purchase Order' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import { useI18n } from '../composables/useI18n'
import { api } from '../api'
import { formatCurrencyWithDecimals } from '../utils/currency'

const { translateProductName, currentCurrency } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create'
  }
})

const emit = defineEmits(['close', 'po-created'])

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const emptyForm = () => ({
  supplier_name: '',
  quantity: null,
  unit_cost: null,
  expected_delivery_date: '',
  notes: ''
})

const form = reactive(emptyForm())
const errors = ref({})
const submitting = ref(false)
const submitError = ref(null)

// Reset form/errors every time the modal is (re)opened in create mode so a
// previously-filled PO (or a different backlog item entirely) never bleeds
// into the next one. Watching both isOpen and backlogItem covers the case
// where the modal is reused for a second item without fully closing first.
watch(
  () => [props.isOpen, props.backlogItem],
  ([isOpen]) => {
    if (!isOpen) return
    submitError.value = null
    errors.value = {}
    if (props.mode === 'create') {
      Object.assign(form, emptyForm())
      // Default quantity to the outstanding shortage so the requester
      // doesn't have to recompute quantity_needed - quantity_available.
      form.quantity = shortage.value > 0 ? shortage.value : null
    }
  },
  { immediate: true }
)

const estimatedTotal = computed(() => {
  const qty = Number(form.quantity)
  const cost = Number(form.unit_cost)
  if (!qty || !cost) return 0
  return qty * cost
})

// Per-field validators, shared by the full-form validate() run at submit time
// and by the field-level watchers below that clear an individual error as
// soon as that field becomes valid (without touching other fields' errors).
const fieldValidators = {
  supplier_name: (value) => {
    if (!value || !value.trim()) return 'Supplier name is required'
    return null
  },
  quantity: (value) => {
    if (value === null || value === '') return 'Quantity is required'
    if (Number(value) <= 0) return 'Quantity must be greater than 0'
    return null
  },
  unit_cost: (value) => {
    if (value === null || value === '') return 'Unit cost is required'
    if (Number(value) < 0) return 'Unit cost cannot be negative'
    return null
  },
  expected_delivery_date: (value) => {
    if (!value) return 'Expected delivery date is required'
    return null
  }
}

const validate = () => {
  const errs = {}
  for (const field of Object.keys(fieldValidators)) {
    const message = fieldValidators[field](form[field])
    if (message) errs[field] = message
  }
  errors.value = errs
  return Object.keys(errs).length === 0
}

// Clear a single field's error the moment it becomes valid, so correcting
// one field doesn't wipe or leave stale messages on the others.
const clearFieldErrorIfValid = (field) => {
  if (!errors.value[field]) return
  if (fieldValidators[field](form[field])) return
  const { [field]: _cleared, ...rest } = errors.value
  errors.value = rest
}

watch(() => form.supplier_name, () => clearFieldErrorIfValid('supplier_name'))
watch(() => form.quantity, () => clearFieldErrorIfValid('quantity'))
watch(() => form.unit_cost, () => clearFieldErrorIfValid('unit_cost'))
watch(() => form.expected_delivery_date, () => clearFieldErrorIfValid('expected_delivery_date'))

const submit = async () => {
  if (submitting.value) return
  if (!validate()) return

  submitting.value = true
  submitError.value = null
  try {
    const payload = {
      // backlog_item_id isn't a user-editable form field — it comes from the
      // shortage row the modal was opened from, and the backend needs it to
      // link the created PO back to that backlog entry.
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.supplier_name.trim(),
      quantity: Number(form.quantity),
      unit_cost: Number(form.unit_cost),
      expected_delivery_date: form.expected_delivery_date,
      notes: form.notes ? form.notes.trim() : undefined
    }
    const created = await api.createPurchaseOrder(payload)
    emit('po-created', created)
  } catch (err) {
    submitError.value = err.response?.data?.detail || 'Failed to create purchase order. Please try again.'
    console.error(err)
  } finally {
    submitting.value = false
  }
}

const close = () => {
  emit('close')
}

const totalCost = computed(() => {
  const po = props.backlogItem?.purchase_order
  if (!po) return 0
  return (po.quantity || 0) * (po.unit_cost || 0)
})

// PO status values are backend-defined and not formally typed on the
// frontend; map the ones we know about to the shared badge palette and
// fall back to 'info' for anything unrecognized rather than guessing.
const statusBadgeClass = computed(() => {
  const status = (props.backlogItem?.purchase_order?.status || '').toLowerCase()
  if (['received', 'delivered', 'completed'].includes(status)) return 'success'
  if (['pending', 'ordered', 'processing'].includes(status)) return 'warning'
  if (['cancelled', 'canceled', 'rejected'].includes(status)) return 'danger'
  return 'info'
})

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'N/A'
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.shortage-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.shortage-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.shortage-title-section {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.5rem 0;
}

.item-sku {
  font-size: 0.875rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
}

.priority-badge {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.priority-badge.high {
  background: #fecaca;
  color: #991b1b;
}

.priority-badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.priority-badge.low {
  background: #dbeafe;
  color: #1e40af;
}

.shortage-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-card {
  padding: 1.25rem;
  border-radius: 10px;
  border: 2px solid;
}

.summary-card.danger {
  border-color: #fecaca;
  background: #fef2f2;
}

.summary-card.warning {
  border-color: #fed7aa;
  background: #fffbeb;
}

.summary-card.info {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.summary-card.neutral {
  border-color: #e2e8f0;
  background: #f8fafc;
}

.summary-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
}

.summary-card.danger .summary-value {
  color: #dc2626;
}

.summary-card.warning .summary-value {
  color: #f59e0b;
}

.summary-card.info .summary-value {
  color: #2563eb;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item.notes-item {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.info-value.order-id {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.no-po-data {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* Create-mode form */
.po-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: flex;
  gap: 1.25rem;
}

.form-row .form-group {
  flex: 1;
  min-width: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #475569;
}

.form-input,
.form-textarea {
  padding: 0.625rem 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  font-family: inherit;
  color: #0f172a;
  transition: border-color 0.15s ease;
  width: 100%;
}

.form-textarea {
  resize: vertical;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-input.invalid,
.form-textarea.invalid {
  border-color: #ef4444;
}

.field-error {
  font-size: 0.813rem;
  color: #dc2626;
  font-weight: 500;
}

.form-error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}

.estimated-total {
  font-size: 0.938rem;
  color: #475569;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem 1rem;
}

.estimated-total strong {
  color: #0f172a;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #3b82f6;
  border: 1px solid #3b82f6;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
  border-color: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
