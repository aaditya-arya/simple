import React, { useState } from 'react';
import { X, UploadCloud, CheckCircle2, AlertTriangle, FileText } from 'lucide-react';
import { uploadBulkCSV } from '../services/api';

export function BulkUploadModal({ isOpen, onClose, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
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

  const handleSimulateDemo = async () => {
    setLoading(true);
    const csvContent = "name,latitude,longitude,department_id,camera_type,vms_vendor_id\n" +
      "Surat-RingRoad-New-PTZ-01,21.1965,72.8310,1,ptz,hikvision\n" +
      "Vadodara-Alkapuri-Cam-02,22.3120,73.1750,2,fixed,dahua\n" +
      "Rajkot-Kalawad-ANPR-03,22.2890,70.7650,4,number_plate,milestone";
    
    const demoBlob = new Blob([csvContent], { type: 'text/csv' });
    const demoFile = new File([demoBlob], "demo_50_gujarat_cameras_onboarding.csv");
    
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
        width: '560px',
        maxHeight: '90vh',
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
            <UploadCloud size={20} color="#2563eb" />
            <h2 style={{ fontSize: '16px', fontWeight: '700', color: '#0f172a' }}>
              Bulk Camera Onboarding Engine
            </h2>
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
          
          {/* Dropzone */}
          <div style={{
            border: '2px dashed #cbd5e1',
            borderRadius: '8px',
            padding: '30px 20px',
            textAlign: 'center',
            backgroundColor: '#f8fafc',
            cursor: 'pointer'
          }}>
            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileChange}
              style={{ display: 'none' }}
              id="file-upload"
            />
            <label htmlFor="file-upload" style={{ cursor: 'pointer' }}>
              <FileText size={36} color="#2563eb" style={{ margin: '0 auto 10px auto' }} />
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#0f172a' }}>
                {file ? file.name : "Click to select or drag CSV / Excel file"}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Supports standard statewide schema with Lat, Lon, Department, and VMS parameters
              </div>
            </label>
          </div>

          {/* Quick Demo Button */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              onClick={handleSimulateDemo}
              disabled={loading}
              style={{
                backgroundColor: '#eff6ff',
                border: '1px solid #bfdbfe',
                color: '#1d4ed8',
                padding: '8px 14px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: '700',
                cursor: 'pointer'
              }}
            >
              ⚡ Quick Load 50 Demo Cameras
            </button>

            <button
              onClick={handleUpload}
              disabled={!file || loading}
              style={{
                backgroundColor: file ? '#2563eb' : '#94a3b8',
                color: '#ffffff',
                border: 'none',
                padding: '8px 20px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: '700',
                cursor: file ? 'pointer' : 'not-allowed',
                boxShadow: file ? '0 2px 6px rgba(37, 99, 235, 0.3)' : 'none'
              }}
            >
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <CheckCircle2 size={16} color="#10b981" />
                <span style={{ fontSize: '13px', fontWeight: '700', color: '#166534' }}>
                  Ingestion Complete: {result.successfully_onboarded} / {result.total_processed} Cameras Validated
                </span>
              </div>

              {result.errors && result.errors.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <div style={{ fontSize: '11px', fontWeight: '700', color: '#b91c1c', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Row-Level Diagnostics & Rejections ({result.failed_count}):
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '100px', overflowY: 'auto' }}>
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
