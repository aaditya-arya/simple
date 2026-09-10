import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { MapDashboard } from './components/MapDashboard';
import { CameraInspector } from './components/CameraInspector';
import { LiveStreamModal } from './components/LiveStreamModal';
import { BulkUploadModal } from './components/BulkUploadModal';
import { GapAnalysisModal } from './components/GapAnalysisModal';
import { fetchCamerasGeoJSON, fetchGapAnalysis } from './services/api';

export function App() {
  const [selectedPersona, setSelectedPersona] = useState('all');
  const [selectedCity, setSelectedCity] = useState('all');
  const [geoData, setGeoData] = useState(null);
  const [gapData, setGapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [liveStreamCamera, setLiveStreamCamera] = useState(null);

  // Layer Toggles
  const [showCoverageBuffers, setShowCoverageBuffers] = useState(true);
  const [showGapZones, setShowGapZones] = useState(false);
  const [showAgeingAlerts, setShowAgeingAlerts] = useState(false);

  // Modals
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);
  const [isGapModalOpen, setIsGapModalOpen] = useState(false);
  const [isLiveModalOpen, setIsLiveModalOpen] = useState(false);

  const loadData = () => {
    setLoading(true);
    const filters = {};
    if (selectedPersona !== 'all') {
      filters.department_id = selectedPersona;
    }
    if (selectedCity !== 'all') {
      filters.city = selectedCity;
    }

    Promise.all([
      fetchCamerasGeoJSON(filters),
      fetchGapAnalysis(selectedPersona === 'all' ? null : selectedPersona)
    ]).then(([cams, gaps]) => {
      setGeoData(cams);
      setGapData(gaps);
      setLoading(false);
    });
  };

  useEffect(() => {
    loadData();
  }, [selectedPersona, selectedCity]);

  const totalCams = geoData?.total_count || 0;
  const sentinelCount = geoData?.sentinel_live_count || 30;

  const handleOpenLiveStream = (camera) => {
    setLiveStreamCamera(camera);
    setIsLiveModalOpen(true);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden', backgroundColor: '#f8fafc' }}>
      {/* Top Light Navbar */}
      <Navbar
        selectedPersona={selectedPersona}
        onPersonaChange={setSelectedPersona}
        selectedCity={selectedCity}
        onCityChange={setSelectedCity}
        totalCameras={totalCams}
        sentinelLiveCount={sentinelCount}
        onOpenBulkUpload={() => setIsBulkModalOpen(true)}
        onOpenGapModal={() => setIsGapModalOpen(true)}
        showCoverageBuffers={showCoverageBuffers}
        setShowCoverageBuffers={setShowCoverageBuffers}
        showGapZones={showGapZones}
        setShowGapZones={setShowGapZones}
        showAgeingAlerts={showAgeingAlerts}
        setShowAgeingAlerts={setShowAgeingAlerts}
      />

      {/* Main Map Body & Inspector */}
      <div style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden' }}>
        <MapDashboard
          geoData={geoData}
          gapData={gapData}
          selectedCity={selectedCity}
          selectedCamera={selectedCamera}
          onSelectCamera={setSelectedCamera}
          onOpenLiveStream={handleOpenLiveStream}
          showCoverageBuffers={showCoverageBuffers}
          showGapZones={showGapZones}
          showAgeingAlerts={showAgeingAlerts}
        />

        {/* Right Camera Inspector Sidebar */}
        {selectedCamera && (
          <CameraInspector
            camera={selectedCamera}
            onClose={() => setSelectedCamera(null)}
            onOpenLiveStream={handleOpenLiveStream}
          />
        )}
      </div>

      {/* Single Live Stream Player Modal */}
      <LiveStreamModal
        camera={liveStreamCamera}
        isOpen={isLiveModalOpen}
        onClose={() => setIsLiveModalOpen(false)}
      />

      {/* Bulk Upload Modal */}
      <BulkUploadModal
        isOpen={isBulkModalOpen}
        onClose={() => setIsBulkModalOpen(false)}
        onUploadSuccess={loadData}
      />

      {/* High-Readability Gap Analysis Matrix Modal */}
      <GapAnalysisModal
        isOpen={isGapModalOpen}
        onClose={() => setIsGapModalOpen(false)}
        selectedDeptId={selectedPersona}
      />
    </div>
  );
}

export default App;
