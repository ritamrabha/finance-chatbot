import sampleManifest from '../data/sampleManifest.json';

export function getSampleInvoices() {
  return sampleManifest.map((item, idx) => ({
    id: idx + 1,
    file: item.file,
    vendor: item.vendor,
    invoice_number: item.invoice_number,
    date: item.date,
    total: item.total,
    currency: item.currency,
    isPlantedDuplicate: !!item.duplicate_of,
    duplicateOf: item.duplicate_of
  }));
}

export function generateExtractionFromSample(sample) {
  const isINR = sample.currency === 'INR';
  const subtotal = Math.round((sample.total / 1.18) * 100) / 100;
  const tax = Math.round((sample.total - subtotal) * 100) / 100;

  return {
    vendor_name: sample.vendor,
    vendor_canonical: sample.vendor,
    invoice_number: sample.invoice_number,
    invoice_date: sample.date,
    currency: sample.currency,
    subtotal: subtotal,
    tax: tax,
    total: sample.total,
    tax_type: isINR ? 'GST (IGST 18%)' : 'VAT 20%',
    confidence: 0.99,
    source_file: sample.file,
    line_items: [
      {
        description: `${sample.vendor} Services & Deliverables Ref: ${sample.invoice_number}`,
        quantity: 1,
        unit_price: subtotal,
        amount: subtotal
      }
    ]
  };
}
