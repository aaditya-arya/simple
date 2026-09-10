import React, { useEffect, useRef, useState } from 'react';
import Hls from 'hls.js';
import { X, Play, Pause, Video, Radio, Shield, AlertCircle, RefreshCw, Layers, Cpu, Activity } from 'lucide-react';

export function LiveStreamModal({ camera, isOpen, onClose }) {
  if (!isOpen || !camera) return null;

  const p = camera.properties;
  const isSentinel = p.is_sentinel_live;
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const wsRef = useRef(null);

  // Host configuration state
  const defaultHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
  const [sandboxHost, setSandboxHost] = useState(defaultHost);
  const [streamStatus, setStreamStatus] = useState('connecting');
  const [isPlaying, setIsPlaying] = useState(true);
  const [aiDetectionOverlay, setAiDetectionOverlay] = useState(true);
  
  // Real-time Dynamic AI Inference Detections from Backend WebSocket
  const [detections, setDetections] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [liveFps, setLiveFps] = useState(30.0);
  const [currentPts, setCurrentPts] = useState(14280);

  const cameraId = p.sentinel_id || p.camera_id || 1;
  const hlsUrl = p.sentinel_hls_url 
    ? p.sentinel_hls_url.replace('sentinel-grid.internal', sandboxHost)
    : `http://${sandboxHost}/live/stream/${cameraId}/index.m3u8`;

  const rtspUrl = p.sentinel_rtsp_url
    ? p.sentinel_rtsp_url.replace('sentinel-grid.internal', sandboxHost)
    : `rtsp://${sandboxHost}:8554/stream/${cameraId}`;

  const webrtcUrl = p.sentinel_webrtc_url
    ? p.sentinel_webrtc_url.replace('sentinel-grid.internal', sandboxHost)
    : `http://${sandboxHost}:8889/stream/${cameraId}/whep`;

  // 1. Attach Real HLS Stream via hls.js
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !hlsUrl) return;

    setStreamStatus('connecting');

    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    let hls;
    if (Hls.isSupported()) {
      hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90
      });
      hlsRef.current = hls;

      hls.loadSource(hlsUrl);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.muted = true;
        video.play()
          .then(() => {
            setStreamStatus('playing');
            setIsPlaying(true);
          })
          .catch((err) => {
            console.log("Autoplay deferred:", err);
            setStreamStatus('playing');
          });
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              setStreamStatus('error');
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              hls.recoverMediaError();
              break;
            default:
              hls.destroy();
              break;
          }
        }
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = hlsUrl;
      video.addEventListener('loadedmetadata', () => {
        video.muted = true;
        video.play()
          .then(() => setStreamStatus('playing'))
          .catch(() => {});
      });
    }

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, [hlsUrl, isOpen]);

  // 2. Connect to Backend WebSocket for Live YOLOv8 Inference Coordinates
  useEffect(() => {
    if (!isOpen) return;

    const wsUrl = `ws://${sandboxHost === 'localhost' ? '127.0.0.1' : sandboxHost}:8000/api/v1/ws/inference/${cameraId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
      console.log(`🔌 Connected to YOLOv8 Inference WebSocket for Cam #${cameraId}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.detections) {
          setDetections(data.detections);
        }
        if (data.pts_ms) {
          setCurrentPts(data.pts_ms);
        }
        if (data.fps) {
          setLiveFps(data.fps);
        }
      } catch (err) {
        console.warn("WebSocket parse error:", err);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    ws.onerror = (err) => {
      console.warn("WebSocket stream notice:", err);
      setWsConnected(false);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [cameraId, sandboxHost, isOpen]);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (isPlaying) {
      video.pause();
      setIsPlaying(false);
    } else {
      video.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.75)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2500,
      backdropFilter: 'blur(6px)'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid #cbd5e1',
        borderRadius: '12px',
        width: '760px',
        maxHeight: '94vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.3)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '14px 20px',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#f8fafc'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              backgroundColor: '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Video size={18} color="#ffffff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '15px', fontWeight: '700', color: '#0f172a', margin: 0 }}>
                  {p.name}
                </h2>
                <span style={{
                  fontSize: '10px',
                  fontWeight: '700',
                  backgroundColor: '#eff6ff',
                  color: '#1d4ed8',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  border: '1px solid #bfdbfe'
                }}>
                  {isSentinel ? "SENTINEL SANDBOX GRID" : "VMS FEDERATED STREAM"}
                </span>
                <span style={{
                  fontSize: '10px',
                  fontWeight: '700',
                  backgroundColor: wsConnected ? '#ecfdf5' : '#fffbeb',
                  color: wsConnected ? '#047857' : '#b45309',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  border: wsConnected ? '1px solid #a7f3d0' : '1px solid #fde68a',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <Cpu size={11} />
                  {wsConnected ? "YOLOv8 RTSP Engine: LIVE" : "Connecting AI..."}
                </span>
              </div>
              <p style={{ fontSize: '11px', color: '#64748b', margin: 0 }}>
                {p.address} • {p.city}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Video Player & Dynamic AI Bounding Box Canvas */}
        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          
          <div style={{
            position: 'relative',
            width: '100%',
            height: '360px',
            backgroundColor: '#000000',
            borderRadius: '8px',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
          }}>
            {/* Real HTML5 Video Element decoded by hls.js */}
            <video
              ref={videoRef}
              playsInline
              muted
              autoPlay
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                backgroundColor: '#000000'
              }}
            />

            {/* Dynamic AI Detections from Backend WebSocket */}
            {aiDetectionOverlay && isPlaying && detections.map((det) => (
              <div
                key={det.track_id}
                style={{
                  position: 'absolute',
                  top: `${det.y_pct}%`,
                  left: `${det.x_pct}%`,
                  width: `${det.w_pct}%`,
                  height: `${det.h_pct}%`,
                  border: det.is_target ? '2px solid #10b981' : '1.5px dashed #38bdf8',
                  borderRadius: '4px',
                  backgroundColor: det.is_target ? 'rgba(16, 185, 129, 0.15)' : 'rgba(56, 189, 248, 0.08)',
                  boxShadow: det.is_target ? '0 0 12px rgba(16, 185, 129, 0.5)' : 'none',
                  pointerEvents: 'none',
                  zIndex: 10,
                  transition: 'all 0.033s linear'
                }}
              >
                <div style={{
                  position: 'absolute',
                  top: '-18px',
                  left: '-2px',
                  backgroundColor: det.is_target ? '#10b981' : '#0284c7',
                  color: '#ffffff',
                  fontSize: '9px',
                  fontWeight: '700',
                  padding: '1px 5px',
                  borderRadius: '2px',
                  letterSpacing: '0.3px',
                  whiteSpace: 'nowrap'
                }}>
                  {det.is_target 
                    ? `TARGET: ${det.plate_number} [${Math.round(det.confidence * 100)}%]` 
                    : `${det.class_name.toUpperCase()} [${Math.round(det.confidence * 100)}%]`}
                </div>
              </div>
            ))}

            {/* Live OSD Overlay (PTS Presentation Timestamps & FPS) */}
            <div style={{
              position: 'absolute',
              top: '12px',
              left: '14px',
              backgroundColor: 'rgba(15, 23, 42, 0.85)',
              backdropFilter: 'blur(4px)',
              padding: '4px 10px',
              borderRadius: '4px',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#f8fafc',
              fontSize: '11px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              zIndex: 15
            }}>
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: streamStatus === 'playing' ? '#10b981' : '#f59e0b'
              }} />
              <span>LIVE • {p.stream_codec || 'H.264'}</span>
              <span style={{ color: '#64748b' }}>|</span>
              <span style={{ color: '#38bdf8' }}>PTS: {currentPts} ms</span>
              <span style={{ color: '#64748b' }}>|</span>
              <span style={{ color: '#34d399' }}>{liveFps.toFixed(1)} FPS</span>
            </div>

            {/* Tag Badge */}
            <div style={{
              position: 'absolute',
              top: '12px',
              right: '14px',
              backgroundColor: 'rgba(15, 23, 42, 0.85)',
              padding: '4px 8px',
              borderRadius: '4px',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#f8fafc',
              fontSize: '10px',
              fontWeight: '700',
              zIndex: 15
            }}>
              {detections.length} VEHICLES DETECTED
            </div>

            {/* Stream Connecting State */}
            {streamStatus === 'connecting' && (
              <div style={{
                position: 'absolute',
                inset: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.65)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                gap: '8px',
                zIndex: 5
              }}>
                <RefreshCw size={24} color="#3b82f6" style={{ animation: 'spin 1.5s linear infinite' }} />
                <span style={{ fontSize: '12px', fontWeight: '600' }}>
                  Attaching HLS Stream: {hlsUrl}
                </span>
              </div>
            )}

            {/* Bottom Stream Control Bar */}
            <div style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              padding: '8px 14px',
              backgroundColor: 'rgba(15, 23, 42, 0.9)',
              backdropFilter: 'blur(6px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderTop: '1px solid #334155',
              zIndex: 15
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  onClick={togglePlay}
                  style={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '4px',
                    color: '#f8fafc',
                    padding: '4px 8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '11px',
                    fontWeight: '600'
                  }}
                >
                  {isPlaying ? <Pause size={12} /> : <Play size={12} />}
                  {isPlaying ? "Pause Stream" : "Resume"}
                </button>

                <button
                  onClick={() => setAiDetectionOverlay(!aiDetectionOverlay)}
                  style={{
                    backgroundColor: aiDetectionOverlay ? '#064e3b' : '#1e293b',
                    border: '1px solid',
                    borderColor: aiDetectionOverlay ? '#10b981' : '#475569',
                    borderRadius: '4px',
                    color: aiDetectionOverlay ? '#6ee7b7' : '#94a3b8',
                    padding: '4px 8px',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: '600'
                  }}
                >
                  AI Overlay: {aiDetectionOverlay ? "ENABLED (YOLOv8)" : "DISABLED"}
                </button>
              </div>

              <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                Transport: <strong style={{ color: '#38bdf8' }}>HLS m3u8 + WebSocket Stream</strong>
              </div>
            </div>
          </div>

          {/* Stream Architecture & Integration Contract */}
          <div style={{
            backgroundColor: '#f8fafc',
            borderRadius: '8px',
            padding: '12px 14px',
            border: '1px solid #e2e8f0',
            fontSize: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <strong style={{ color: '#0f172a' }}>Live Stream Protocol Matrix</strong>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '11px', color: '#64748b' }}>Host IP:</span>
                <input
                  type="text"
                  value={sandboxHost}
                  onChange={(e) => setSandboxHost(e.target.value)}
                  style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    border: '1px solid #cbd5e1',
                    fontSize: '11px',
                    width: '140px',
                    backgroundColor: '#ffffff'
                  }}
                  title="Configure exact Sandbox Gateway IP / Host"
                />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '6px 10px',
                borderRadius: '6px',
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0'
              }}>
                <div>
                  <strong style={{ color: '#d97706' }}>Frontend HLS (.m3u8):</strong>
                  <code style={{ marginLeft: '8px', color: '#334155', fontSize: '11px' }}>
                    {hlsUrl}
                  </code>
                </div>
                <span style={{ fontSize: '10px', fontWeight: '700', color: '#059669', backgroundColor: '#ecfdf5', padding: '2px 6px', borderRadius: '4px' }}>
                  ACTIVE IN HTML5 &lt;video&gt;
                </span>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '6px 10px',
                borderRadius: '6px',
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0'
              }}>
                <div>
                  <strong style={{ color: '#059669' }}>Backend RTSP (TCP):</strong>
                  <code style={{ marginLeft: '8px', color: '#334155', fontSize: '11px' }}>
                    {rtspUrl}
                  </code>
                </div>
                <span style={{ fontSize: '10px', color: '#64748b' }}>
                  YOLOv8 OpenCV Machine Consumer
                </span>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '6px 10px',
                borderRadius: '6px',
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0'
              }}>
                <div>
                  <strong style={{ color: '#2563eb' }}>WebSocket Stream:</strong>
                  <code style={{ marginLeft: '8px', color: '#334155', fontSize: '11px' }}>
                    ws://{sandboxHost}:8000/api/v1/ws/inference/{cameraId}
                  </code>
                </div>
                <span style={{ fontSize: '10px', color: '#64748b' }}>
                  30 FPS Live Bounding Boxes
                </span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
