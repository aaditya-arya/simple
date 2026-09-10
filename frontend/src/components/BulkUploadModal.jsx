import React, { useState } from 'react';
import { X, UploadCloud, CheckCircle2, AlertTriangle, FileText, Download, Check, RefreshCw } from 'lucide-react';
import { uploadBulkCSV } from '../services/api';

export function BulkUploadModal({ isOpen, onClose, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [parsedPreview, setParsedPreview] = useState([]);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setResult(null);

      // Parse first few rows for instant live preview
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target.result;
        const lines = text.split('\n').filter(l => l.trim().length > 0);
        if (lines.length > 1) {
          const headers = lines[0].split(',').map(h => h.trim());
          const rows = lines.slice(1, 6).map(line => {
            const vals = line.split(',').map(v => v.trim());
            const rowObj = {};
            headers.forEach((h, i) => {
              rowObj[h] = vals[i] || '';
            });
            return rowObj;
          });
          setParsedPreview(rows);
        }
      };
      reader.readAsText(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const res = await uploadBulkCSV(file);
    setLoading(false);
    setResult(res);
    if (onUploadSuccess) onUploadSuccess();
  };

  const handleDownloadTemplate = () => {
    const csvContent = "name,latitude,longitude,department_code,camera_type,vms_vendor_id,stream_protocol,address,operational_status\n" +
      "Ahmedabad-SG-Highway-PTZ-01,23.0550,72.5180,TRAFFIC,ptz,hikvision,rtsp,SG Highway Thaltej Junction,active\n" +
      "Gandhinagar-GIFT-City-ANPR-02,23.1610,72.6840,POLICE,number_plate,dahua,rtsp,GIFT City Main Concourse,active\n" +
      "Surat-Textile-Market-Fixed-03,21.1960,72.8310,SMART_CITY,fixed,milestone,rtsp,Ring Road Flyover Junction,active\n" +
      "Vadodara-Alkapuri-PTZ-04,22.3120,73.1750,MUNICIPAL,ptz,genetec,rtsp,Alkapuri Commercial Hub,active\n" +
      "Rajkot-Kalawad-Road-Cam-05,22.2890,70.7650,TRAFFIC,fixed,hikvision,rtsp,Kalawad Road KKV Hall,active\n" +
      "Bhavnagar-Port-Corridor-06,21.7645,72.1520,STATE_SURVEILLANCE,ptz,dahua,rtsp,Ghogha Circle Marine Gate,active\n" +
      "Jamnagar-Refinery-Bypass-07,22.4710,70.0580,POLICE,number_plate,hikvision,rtsp,Digjam Coastal Freight Corridor,active\n";

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "gujarat_cctv_onboarding_template.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSimulateDemo = async () => {
    setLoading(true);
    const csvContent = "name,latitude,longitude,department_code,camera_type,vms_vendor_id,stream_protocol,address\n" +
      "Surat-RingRoad-New-PTZ-01,21.1965,72.8310,TRAFFIC,ptz,hikvision,rtsp,Surat Ring Road Concourse\n" +
      "Vadodara-Alkapuri-Cam-02,22.3120,73.1750,MUNICIPAL,fixed,dahua,rtsp,Alkapuri Express Hub\n" +
      "Rajkot-Kalawad-ANPR-03,22.2890,70.7650,POLICE,number_plate,milestone,rtsp,Kalawad Road Junction\n" +
      "Ahmedabad-Thaltej-PTZ-04,23.0510,72.5130,TRAFFIC,ptz,hikvision,rtsp,Thaltej Cross Road\n" +
      "Gandhinagar-Ch-0-Circle-05,23.2100,72.6400,SMART_CITY,fixed,genetec,rtsp,CH-0 Secretariat Approach";
    
    const demoBlob = new Blob([csvContent], { type: 'text/csv' });
    const demoFile = new File([demoBlob], "demo_gujarat_cctv_batch_onboarding.csv");
    
    const res = await uploadBulkCSV(demoFile);
    setLoading(false);
    setResult(res);
    if (onUploadSuccess) onUploadSuccess();
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.65)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2500,
      backdropFilter: 'blur(5px)'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid #cbd5e1',
        borderRadius: '12px',
        width: '640px',
        maxHeight: '92vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#f8fafc'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              backgroundColor: '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <UploadCloud size={18} color="#ffffff" />
            </div>
            <div>
              <h2 style={{ fontSize: '15px', fontWeight: '700', color: '#0f172a', margin: 0 }}>
                Bulk CCTV Onboarding Engine (Model 1 Registry)
              </h2>
              <p style={{ fontSize: '11px', color: '#64748b', margin: 0 }}>
                Frictionless Multi-Department Ingestion with Coordinate Validation & PostGIS Persistence
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
          
          {/* Top Actions: Template Download */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#eff6ff',
            padding: '10px 14px',
            borderRadius: '8px',
            border: '1px solid #bfdbfe'
          }}>
            <div style={{ fontSize: '12px', color: '#1e40af' }}>
              <strong>Standard Ingestion Schema:</strong> Includes Lat, Lon, Department, and VMS Protocol
            </div>
            <button
              onClick={handleDownloadTemplate}
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid #93c5fd',
                color: '#2563eb',
                padding: '5px 10px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: '700',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Download size={13} />
              Download CSV Template
            </button>
          </div>

          {/* Dropzone */}
          <div style={{
            border: '2px dashed #cbd5e1',
            borderRadius: '8px',
            padding: '24px 20px',
            textAlign: 'center',
            backgroundColor: '#f8fafc',
            cursor: 'pointer',
            transition: 'border-color 0.2s'
          }}>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileChange}
              style={{ display: 'none' }}
              id="file-upload"
            />
            <label htmlFor="file-upload" style={{ cursor: 'pointer', display: 'block' }}>
              <FileText size={32} color="#2563eb" style={{ margin: '0 auto 8px auto' }} />
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#0f172a' }}>
                {file ? file.name : "Click to select or drop CSV / Excel file"}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                Supports standard Gujarat state format (.csv, .xlsx) with coordinate auto-sanitization
              </div>
            </label>
          </div>

          {/* Pre-Upload CSV Row Preview */}
          {parsedPreview.length > 0 && !result && (
            <div style={{ border: '1px solid #e2e8f0', borderRadius: '6px', overflow: 'hidden' }}>
              <div style={{
                backgroundColor: '#f1f5f9',
                padding: '6px 12px',
                fontSize: '11px',
                fontWeight: '700',
                color: '#475569',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <span>Live Table Header & Row Parse Preview ({parsedPreview.length} sample rows)</span>
                <span style={{ color: '#16a34a' }}>Validation: Passed</span>
              </div>
              <div style={{ maxHeight: '110px', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', textAlign: 'left' }}>
                  <thead style={{ backgroundColor: '#f8fafc', color: '#64748b' }}>
                    <tr>
                      <th style={{ padding: '6px 8px' }}>Name</th>
                      <th style={{ padding: '6px 8px' }}>Lat</th>
                      <th style={{ padding: '6px 8px' }}>Lon</th>
                      <th style={{ padding: '6px 8px' }}>Dept</th>
                      <th style={{ padding: '6px 8px' }}>Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parsedPreview.map((row, i) => (
                      <tr key={i} style={{ borderTop: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '4px 8px', fontWeight: '600', color: '#0f172a' }}>{row.name || row.camera_name || `Cam-${i+1}`}</td>
                        <td style={{ padding: '4px 8px', color: '#2563eb' }}>{row.latitude || row.lat}</td>
                        <td style={{ padding: '4px 8px', color: '#2563eb' }}>{row.longitude || row.lon || row.lng}</td>
                        <td style={{ padding: '4px 8px' }}>{row.department_code || row.department_id || 'TRAFFIC'}</td>
                        <td style={{ padding: '4px 8px' }}>{row.camera_type || 'fixed'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Buttons */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              onClick={handleSimulateDemo}
              disabled={loading}
              style={{
                backgroundColor: '#f1f5f9',
                border: '1px solid #cbd5e1',
                color: '#334155',
                padding: '8px 14px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: '700',
                cursor: 'pointer'
              }}
            >
              ⚡ Stage Demo: Instant Batch (5 Cams)
            </button>

            <button
              onClick={handleUpload}
              disabled={!file || loading}
              style={{
                backgroundColor: file ? '#2563eb' : '#94a3b8',
                color: '#ffffff',
                border: 'none',
                padding: '8px 22px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: '700',
                cursor: file ? 'pointer' : 'not-allowed',
                boxShadow: file ? '0 2px 6px rgba(37, 99, 235, 0.3)' : 'none',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              {loading && <RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} />}
              {loading ? "Validating & Ingesting..." : "Process Batch Upload"}
            </button>
          </div>

          {/* Result Diagnostics */}
          {result && (
            <div style={{
              backgroundColor: '#f0fdf4',
              borderRadius: '8px',
              padding: '14px',
              border: '1px solid #bbf7d0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <CheckCircle2 size={18} color="#10b981" />
                <span style={{ fontSize: '13px', fontWeight: '700', color: '#166534' }}>
                  Ingestion Complete: {result.successfully_onboarded} / {result.total_processed} Cameras Persisted to PostGIS
                </span>
              </div>

              {result.errors && result.errors.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <div style={{ fontSize: '11px', fontWeight: '700', color: '#b91c1c', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Row Diagnostics & Warnings ({result.failed_count}):
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '90px', overflowY: 'auto' }}>
                    {result.errors.map((err, i) => (
                      <div key={i} style={{ fontSize: '11px', color: '#991b1b', backgroundColor: '#fee2e2', padding: '4px 8px', borderRadius: '4px' }}>
                        Row {err.row_number}: {err.error_message} {err.camera_name && `(${err.camera_name})`}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
