import React, { useEffect, useRef, useState } from 'react';
import Hls from 'hls.js';
import { X, Play, Pause, Video, Radio, Shield, AlertCircle, RefreshCw, Layers, Cpu, Activity, CheckCircle2, ShieldX } from 'lucide-react';

export function LiveStreamModal({ camera, isOpen, onClose }) {
  const p = camera?.properties || {};
  const isSentinel = p.is_sentinel_live;
  const isOffline = p.connectivity_status === 'offline';
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const wsRef = useRef(null);
  const wsRetryRef = useRef(null);

  // Host configuration state
  const defaultHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
  const [sandboxHost, setSandboxHost] = useState(defaultHost);
  const [streamStatus, setStreamStatus] = useState('connecting'); // 'connecting' | 'playing_hls' | 'offline'
  const [isPlaying, setIsPlaying] = useState(true);
  const [aiDetectionOverlay, setAiDetectionOverlay] = useState(true);
  
  // Real-time Dynamic AI Inference Detections from Backend WebSocket
  const [detections, setDetections] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [liveFps, setLiveFps] = useState(30.0);
  const [currentPts, setCurrentPts] = useState(0);

  const [customStreamUrl, setCustomStreamUrl] = useState('');
  const [activeProtocol, setActiveProtocol] = useState('webrtc'); // 'webrtc' | 'hls' | 'direct'
  const pcRef = useRef(null);

  // Map to active camera channel (Sentinel 1-30 or local channel 1)
  const rawId = p.sentinel_id || p.camera_id || 1;
  const cameraId = (rawId >= 1 && rawId <= 30) ? rawId : 1;
  const isLocalHost = sandboxHost === 'localhost' || sandboxHost === '127.0.0.1';
  const streamChannel = isLocalHost ? 1 : cameraId;

  const localHlsUrl = `http://${sandboxHost}:8888/stream/${streamChannel}/index.m3u8`;
  const sentinelProxyHlsUrl = `http://${sandboxHost}/live/stream/${streamChannel}/index.m3u8`;
  
  const hlsUrl = customStreamUrl && customStreamUrl.includes('.m3u8')
    ? customStreamUrl
    : (isLocalHost
      ? localHlsUrl 
      : (p.sentinel_hls_url ? p.sentinel_hls_url.replace('sentinel-grid.internal', sandboxHost) : sentinelProxyHlsUrl));

  const rtspUrl = p.sentinel_rtsp_url
    ? p.sentinel_rtsp_url.replace('sentinel-grid.internal', sandboxHost)
    : `rtsp://${sandboxHost}:8554/stream/${streamChannel}`;

  const webrtcUrl = customStreamUrl && customStreamUrl.includes('/whep')
    ? customStreamUrl
    : (p.sentinel_webrtc_url
      ? p.sentinel_webrtc_url.replace('sentinel-grid.internal', sandboxHost)
      : `http://${sandboxHost}:8889/stream/${streamChannel}/whep`);

  // 1. WebRTC (WHEP) and HLS Stream Lifecycle Manager
  useEffect(() => {
    if (!isOpen) return;

    if (isOffline) {
      setStreamStatus('offline');
      return;
    }

    const video = videoRef.current;
    if (!video) return;

    setStreamStatus('connecting');
    let isCancelled = false;

    // Helper to clean up any existing peer connection
    const closeWebRtc = () => {
      if (pcRef.current) {
        try {
          pcRef.current.close();
        } catch (e) {}
        pcRef.current = null;
      }
    };

    // Helper to clean up HLS instance
    const closeHls = () => {
      if (hlsRef.current) {
        try {
          hlsRef.current.destroy();
        } catch (e) {}
        hlsRef.current = null;
      }
    };

    // Initialize HLS Playback Fallback
    const startHls = () => {
      if (isCancelled) return;
      closeWebRtc();
      closeHls();
      if (video.srcObject) {
        video.srcObject = null;
      }

      if (Hls.isSupported()) {
        const hls = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
          liveSyncDurationCount: 1,
          liveMaxLatencyDurationCount: 2,
          maxBufferLength: 2,
          backBufferLength: 0,
          manifestLoadingTimeOut: 3000,
          levelLoadingTimeOut: 3000,
        });
        hlsRef.current = hls;

        hls.loadSource(hlsUrl);
        hls.attachMedia(video);

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          if (isCancelled) return;
          video.muted = true;
          video.play()
            .then(() => {
              setStreamStatus('playing_hls');
              setIsPlaying(true);
            })
            .catch(() => {
              setStreamStatus('playing_hls');
            });
        });

        hls.on(Hls.Events.ERROR, (event, data) => {
          if (isCancelled) return;
          if (data.fatal) {
            hls.destroy();
            hlsRef.current = null;
            setStreamStatus('offline');
          }
        });
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = hlsUrl;
        video.addEventListener('loadedmetadata', () => {
          if (isCancelled) return;
          video.muted = true;
          video.play()
            .then(() => setStreamStatus('playing_hls'))
            .catch(() => setStreamStatus('offline'));
        });
        video.addEventListener('error', () => {
          if (isCancelled) return;
          setStreamStatus('offline');
        });
      }
    };

    // Initialize Native WebRTC WHEP Playback
    const startWebRtc = async () => {
      closeWebRtc();
      closeHls();
      if (video.srcObject) {
        video.srcObject = null;
      }

      try {
        const pc = new RTCPeerConnection({
          iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
          ],
          bundlePolicy: 'max-bundle'
        });
        pcRef.current = pc;

        pc.addTransceiver('video', { direction: 'recvonly' });
        pc.addTransceiver('audio', { direction: 'recvonly' });

        pc.ontrack = (event) => {
          if (isCancelled) return;
          if (videoRef.current && event.streams && event.streams[0]) {
            videoRef.current.srcObject = event.streams[0];
            videoRef.current.play()
              .then(() => {
                setStreamStatus('playing_webrtc');
                setIsPlaying(true);
              })
              .catch((err) => {
                console.warn("WebRTC Autoplay warning:", err);
                setStreamStatus('playing_webrtc');
              });
          }
        };

        pc.oniceconnectionstatechange = () => {
          if (isCancelled) return;
          if (pc.iceConnectionState === 'failed' || pc.iceConnectionState === 'disconnected') {
            console.warn("WebRTC ICE Disconnected. Falling back to HLS...");
            startHls();
          }
        };

        // Create SDP Offer
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        // POST SDP Offer to WHEP Endpoint
        const whepResponse = await fetch(webrtcUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/sdp',
          },
          body: offer.sdp,
        });

        if (!whepResponse.ok) {
          throw new Error(`WHEP endpoint returned status ${whepResponse.status}`);
        }

        const answerSdp = await whepResponse.text();
        if (isCancelled) return;

        await pc.setRemoteDescription({
          type: 'answer',
          sdp: answerSdp,
        });

        // Set safety timeout: if WebRTC track doesn't attach within 3 seconds, fallback to HLS
        setTimeout(() => {
          if (!isCancelled && pcRef.current && pcRef.current.iceConnectionState !== 'connected' && pcRef.current.iceConnectionState !== 'completed' && streamStatus !== 'playing_webrtc') {
            console.info("WebRTC taking too long to connect, falling back to HLS...");
            startHls();
          }
        }, 3000);

      } catch (err) {
        console.warn(`WebRTC WHEP initiation failed (${err.message}). Auto-switching to HLS fallback...`);
        if (!isCancelled) {
          startHls();
        }
      }
    };

    if (activeProtocol === 'webrtc') {
      startWebRtc();
    } else {
      startHls();
    }

    return () => {
      isCancelled = true;
      closeWebRtc();
      closeHls();
      if (video) {
        video.srcObject = null;
        video.src = "";
      }
    };
  }, [hlsUrl, webrtcUrl, isOpen, isOffline, activeProtocol]);

  // 2. Connect to the backend WebSocket for live YOLOv8 inference coordinates.
  useEffect(() => {
    if (!isOpen || isOffline) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsHost = isLocalHost ? '127.0.0.1' : sandboxHost;
    const wsPort = import.meta.env.VITE_API_PORT || '8005';
    const wsUrl = `${wsProtocol}://${wsHost}:${wsPort}/api/v1/ws/inference/${cameraId}`;
    let stopped = false;
    let retryDelay = 1000;
    const connect = () => {
      if (stopped) return;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
          retryDelay = 1000;
          console.log(`Connected to YOLOv8 Inference WebSocket for Cam #${cameraId}`);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.detections) setDetections(data.detections);
            if (data.pts_ms) setCurrentPts(data.pts_ms);
            if (data.fps) setLiveFps(data.fps);
          } catch (err) {
            console.warn("WebSocket parse error:", err);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          setDetections([]);
          if (!stopped) {
            wsRetryRef.current = window.setTimeout(connect, retryDelay);
            retryDelay = Math.min(retryDelay * 2, 5000);
          }
        };

        ws.onerror = () => {
          setWsConnected(false);
          setDetections([]);
        };
      } catch (e) {
        setWsConnected(false);
        setDetections([]);
      }
    };

    connect();

    return () => {
      stopped = true;
      setDetections([]);
      if (wsRetryRef.current) window.clearTimeout(wsRetryRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [cameraId, sandboxHost, isOpen, isOffline]);

  if (!isOpen || !camera) return null;

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

  const handleRetryHls = () => {
    setStreamStatus('connecting');
    const video = videoRef.current;
    if (video && Hls.isSupported()) {
      if (hlsRef.current) hlsRef.current.destroy();
      const hls = new Hls({ enableWorker: true, lowLatencyMode: true });
      hlsRef.current = hls;
      hls.loadSource(hlsUrl);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.muted = true;
        video.play().then(() => setStreamStatus('playing_hls')).catch(() => {});
      });
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
        width: '780px',
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
              backgroundColor: isOffline ? '#dc2626' : '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {isOffline ? <ShieldX size={18} color="#ffffff" /> : <Video size={18} color="#ffffff" />}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '15px', fontWeight: '700', color: '#0f172a', margin: 0 }}>
                  {p.name}
                </h2>
                <span style={{
                  fontSize: '10px',
                  fontWeight: '700',
                  backgroundColor: isOffline ? '#fef2f2' : streamStatus === 'playing_hls' ? '#ecfdf5' : '#eff6ff',
                  color: isOffline ? '#dc2626' : streamStatus === 'playing_hls' ? '#047857' : '#1d4ed8',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  border: isOffline ? '1px solid #fecaca' : streamStatus === 'playing_hls' ? '1px solid #a7f3d0' : '1px solid #bfdbfe'
                }}>
                  {isOffline ? "ASSET OFFLINE" : streamStatus === 'playing_hls' ? "LIVE HLS FEED (MediaMTX)" : "CONNECTING TO LIVE FEED"}
                </span>
                {!isOffline && (
                  <span style={{
                    fontSize: '10px',
                    fontWeight: '700',
                    backgroundColor: '#ecfdf5',
                    color: '#047857',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    border: '1px solid #a7f3d0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    <Cpu size={11} />
                    {wsConnected ? "YOLOv8 RTSP Engine: LIVE" : "YOLOv8 Real-Time AI"}
                  </span>
                )}
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
          
          {isOffline ? (
            <div style={{
              width: '100%',
              height: '360px',
              backgroundColor: '#1e293b',
              borderRadius: '8px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              gap: '12px',
              padding: '24px',
              textAlign: 'center'
            }}>
              <ShieldX size={48} color="#ef4444" />
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#f87171' }}>
                Connection Refused: CCTV Asset Offline
              </div>
              <div style={{ fontSize: '12px', color: '#94a3b8', maxWidth: '460px' }}>
                Physical camera at <strong>{p.name}</strong> ({p.address}) is currently unreachable.
                Hardware telemetry indicates a power disruption or fiber link failure. Video streaming and AI inference are disabled.
              </div>
            </div>
          ) : (
            <div style={{
              position: 'relative',
              width: '100%',
              aspectRatio: '16 / 9',
              maxHeight: '360px',
              backgroundColor: '#000000',
              borderRadius: '8px',
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
            }}>
              {/* Real HTML5 Video Element */}
              <video
                ref={videoRef}
                playsInline
                muted
                autoPlay
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  backgroundColor: '#000000'
                }}
              />

              {/* Dynamic AI Detections Overlay */}
              {aiDetectionOverlay && isPlaying && streamStatus === 'playing_hls' && wsConnected && detections.map((det) => (
                <div
                  key={det.track_id}
                  style={{
                    position: 'absolute',
                    top: `${det.y_pct}%`,
                    left: `${det.x_pct}%`,
                    width: `${det.w_pct}%`,
                    height: `${det.h_pct}%`,
                    border: det.is_target ? '2.5px solid #10b981' : '2px dashed #38bdf8',
                    borderRadius: '4px',
                    backgroundColor: det.is_target ? 'rgba(16, 185, 129, 0.20)' : 'rgba(56, 189, 248, 0.10)',
                    boxShadow: det.is_target ? '0 0 16px rgba(16, 185, 129, 0.7)' : 'none',
                    pointerEvents: 'none',
                    zIndex: 10,
                    transition: 'all 0.033s linear'
                  }}
                >
                  <div style={{
                    position: 'absolute',
                    top: '-20px',
                    left: '-2px',
                    backgroundColor: det.is_target ? '#10b981' : '#0284c7',
                    color: '#ffffff',
                    fontSize: '10px',
                    fontWeight: '800',
                    padding: '2px 6px',
                    borderRadius: '3px',
                    letterSpacing: '0.4px',
                    whiteSpace: 'nowrap',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
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
                  backgroundColor: streamStatus === 'playing_hls' ? '#10b981' : '#38bdf8'
                }} />
                <span>LIVE • {streamStatus === 'playing_hls' ? 'H.264 (HLS)' : 'H.264 (Direct)'}</span>
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
                {detections.length} TARGETS TRACKED
              </div>

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

                  <button
                    onClick={() => setActiveProtocol(activeProtocol === 'webrtc' ? 'hls' : 'webrtc')}
                    title="Toggle between WebRTC WHEP (ultra low latency) and HLS"
                    style={{
                      backgroundColor: activeProtocol === 'webrtc' ? '#1e3a8a' : '#1e293b',
                      border: '1px solid',
                      borderColor: activeProtocol === 'webrtc' ? '#3b82f6' : '#475569',
                      borderRadius: '4px',
                      color: activeProtocol === 'webrtc' ? '#93c5fd' : '#94a3b8',
                      padding: '4px 8px',
                      cursor: 'pointer',
                      fontSize: '11px',
                      fontWeight: '600',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <span>{activeProtocol === 'webrtc' ? '⚡ WebRTC (WHEP <150ms)' : '📡 HLS (~2s)'}</span>
                  </button>

                  <button
                    onClick={() => {
                      const curr = activeProtocol;
                      setActiveProtocol('hls');
                      setTimeout(() => setActiveProtocol(curr), 50);
                    }}
                    title="Reconnect stream"
                    style={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #475569',
                      borderRadius: '4px',
                      color: '#94a3b8',
                      padding: '4px 8px',
                      cursor: 'pointer',
                      fontSize: '11px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <RefreshCw size={11} />
                    Reconnect
                  </button>
                </div>

                <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                  Transport: <strong style={{ color: '#38bdf8' }}>
                    {streamStatus === 'playing_webrtc' ? '⚡ WebRTC WHEP (<150ms)' : streamStatus === 'playing_hls' ? 'MediaMTX HLS' : 'Connecting Stream...'} + 30 FPS WebSocket
                  </strong>
                </div>
              </div>
            </div>
          )}

          {/* Stream Architecture & Integration Contract */}
          <div style={{
            backgroundColor: '#f8fafc',
            borderRadius: '8px',
            padding: '12px 14px',
            border: '1px solid #e2e8f0',
            fontSize: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <strong style={{ color: '#0f172a' }}>Live Stream Protocol Matrix (Sentinel Contract)</strong>
                <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                  <button
                    onClick={() => { setSandboxHost('localhost'); setCustomStreamUrl(''); }}
                    style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      border: '1px solid',
                      borderColor: sandboxHost === 'localhost' || sandboxHost === '127.0.0.1' ? '#2563eb' : '#cbd5e1',
                      backgroundColor: sandboxHost === 'localhost' || sandboxHost === '127.0.0.1' ? '#eff6ff' : '#ffffff',
                      color: sandboxHost === 'localhost' || sandboxHost === '127.0.0.1' ? '#1d4ed8' : '#64748b',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    ⚡ Local Gateway
                  </button>
                  <button
                    onClick={() => { setSandboxHost('sentinel-grid.internal'); setCustomStreamUrl(''); }}
                    style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      border: '1px solid',
                      borderColor: sandboxHost === 'sentinel-grid.internal' ? '#2563eb' : '#cbd5e1',
                      backgroundColor: sandboxHost === 'sentinel-grid.internal' ? '#eff6ff' : '#ffffff',
                      color: sandboxHost === 'sentinel-grid.internal' ? '#1d4ed8' : '#64748b',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    🏢 Official Sentinel Grid
                  </button>
                  <button
                    onClick={() => { setSandboxHost('192.168.1.25'); setCustomStreamUrl(''); }}
                    style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      border: '1px solid',
                      borderColor: sandboxHost === '192.168.1.25' ? '#2563eb' : '#cbd5e1',
                      backgroundColor: sandboxHost === '192.168.1.25' ? '#eff6ff' : '#ffffff',
                      color: sandboxHost === '192.168.1.25' ? '#1d4ed8' : '#64748b',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    📱 Live IP Cam (192.168.1.25)
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600' }}>Host IP / Gateway:</span>
                <input
                  type="text"
                  value={sandboxHost}
                  onChange={(e) => setSandboxHost(e.target.value)}
                  style={{
                    padding: '3px 8px',
                    borderRadius: '4px',
                    border: '1px solid #cbd5e1',
                    fontSize: '11px',
                    width: '150px',
                    backgroundColor: '#ffffff'
                  }}
                  title="Enter Sentinel Sandbox Gateway IP or localhost or camera IP"
                />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {/* WebRTC WHEP Endpoint */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '6px 10px',
                borderRadius: '6px',
                backgroundColor: activeProtocol === 'webrtc' ? '#eff6ff' : '#ffffff',
                border: activeProtocol === 'webrtc' ? '1px solid #bfdbfe' : '1px solid #e2e8f0'
              }}>
                <div>
                  <strong style={{ color: '#2563eb' }}>Browser WebRTC (WHEP):</strong>
                  <code style={{ marginLeft: '8px', color: '#334155', fontSize: '11px' }}>
                    {webrtcUrl}
                  </code>
                </div>
                <span style={{
                  fontSize: '10px',
                  fontWeight: '700',
                  color: isOffline ? '#dc2626' : streamStatus === 'playing_webrtc' ? '#059669' : '#2563eb',
                  backgroundColor: isOffline ? '#fee2e2' : streamStatus === 'playing_webrtc' ? '#ecfdf5' : '#eff6ff',
                  padding: '2px 6px',
                  borderRadius: '4px'
                }}>
                  {isOffline ? 'OFFLINE' : streamStatus === 'playing_webrtc' ? 'ACTIVE WebRTC (<150ms)' : 'WHEP READY'}
                </span>
              </div>

              {/* HLS Endpoint */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '6px 10px',
                borderRadius: '6px',
                backgroundColor: activeProtocol === 'hls' ? '#fffbeb' : '#ffffff',
                border: activeProtocol === 'hls' ? '1px solid #fde68a' : '1px solid #e2e8f0'
              }}>
                <div>
                  <strong style={{ color: '#d97706' }}>Frontend HLS (.m3u8):</strong>
                  <code style={{ marginLeft: '8px', color: '#334155', fontSize: '11px' }}>
                    {hlsUrl}
                  </code>
                </div>
                <span style={{
                  fontSize: '10px',
                  fontWeight: '700',
                  color: isOffline ? '#dc2626' : streamStatus === 'playing_hls' ? '#059669' : '#d97706',
                  backgroundColor: isOffline ? '#fee2e2' : streamStatus === 'playing_hls' ? '#ecfdf5' : '#fffbeb',
                  padding: '2px 6px',
                  borderRadius: '4px'
                }}>
                  {isOffline ? 'OFFLINE' : streamStatus === 'playing_hls' ? 'ACTIVE HLS' : 'FALLBACK'}
                </span>
              </div>

              {/* Backend RTSP Endpoint */}
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
                  YOLOv8 OpenCV Machine Ingestion
                </span>
              </div>

              {/* WebSocket Pipeline */}
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
                  <strong style={{ color: '#7c3aed' }}>WebSocket AI Pipeline:</strong>
                  <code style={{ marginLeft: '8px', color: '#334155', fontSize: '11px' }}>
                    ws://{sandboxHost === 'localhost' ? '127.0.0.1' : sandboxHost}:{import.meta.env.VITE_API_PORT || '8005'}/api/v1/ws/inference/{cameraId}
                  </code>
                </div>
                <span style={{
                  fontSize: '10px',
                  color: wsConnected ? '#059669' : '#b45309',
                  fontWeight: '600'
                }}>
                  {wsConnected ? '30 FPS Live Bounding Boxes' : 'Waiting for AI connection'}
                </span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
