import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { getMapData } from '../api/client';

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

const DATASETS = ['crime', 'traffic', 'permits', 'code_complaints'];

const DATASET_COLORS = {
  crime: '#e74c3c',
  traffic: '#f39c12',
  permits: '#2ecc71',
  code_complaints: '#3498db',
};

export default function Map({ onNeighborhoodClick, neighborhoods }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [activeDataset, setActiveDataset] = useState('crime');
  const [loading, setLoading] = useState(false);

  // Initialize map
  useEffect(() => {
    if (map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [-97.7431, 30.2672],
      zoom: 11,
    });

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    map.current.on('load', () => {
      // Add neighborhood boundaries layer
      map.current.addSource('neighborhoods', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      map.current.addLayer({
        id: 'neighborhoods-fill',
        type: 'fill',
        source: 'neighborhoods',
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['coalesce', ['get', 'overall_score'], 50],
            0, '#8B0000',
            25, '#e74c3c',
            50, '#f39c12',
            75, '#2ecc71',
            100, '#1a8a4a',
          ],
          'fill-opacity': 0.3,
        },
      });

      map.current.addLayer({
        id: 'neighborhoods-outline',
        type: 'line',
        source: 'neighborhoods',
        paint: {
          'line-color': '#ffffff',
          'line-width': 1,
          'line-opacity': 0.5,
        },
      });

      // Click handler for neighborhoods
      map.current.on('click', 'neighborhoods-fill', (e) => {
        const props = e.features[0].properties;
        if (onNeighborhoodClick) onNeighborhoodClick(props.slug);
      });

      map.current.on('mouseenter', 'neighborhoods-fill', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });

      map.current.on('mouseleave', 'neighborhoods-fill', () => {
        map.current.getCanvas().style.cursor = '';
      });

      // Add incident points layer
      map.current.addSource('incidents', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      map.current.addLayer({
        id: 'incidents-heat',
        type: 'heatmap',
        source: 'incidents',
        paint: {
          'heatmap-weight': 1,
          'heatmap-intensity': 1,
          'heatmap-radius': 15,
          'heatmap-opacity': 0.7,
        },
      });
    });
  }, []);

  // Update neighborhood boundaries when data loads
  useEffect(() => {
    if (!map.current || !neighborhoods) return;

    const updateSource = () => {
      const source = map.current.getSource('neighborhoods');
      if (source) source.setData(neighborhoods);
    };

    if (map.current.loaded()) {
      updateSource();
    } else {
      map.current.on('load', updateSource);
    }
  }, [neighborhoods]);

  // Load incident data when dataset changes
  useEffect(() => {
    if (!map.current) return;

    const loadData = async () => {
      setLoading(true);
      try {
        const bounds = map.current.getBounds();
        const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;
        
        const data = await getMapData(activeDataset, {
          bbox,
          start: '2025-01-01',
        });

        const source = map.current.getSource('incidents');
        if (source) source.setData(data);

        // Update heatmap color based on dataset
        if (map.current.getLayer('incidents-heat')) {
          map.current.setPaintProperty(
            'incidents-heat',
            'heatmap-color',
            [
              'interpolate',
              ['linear'],
              ['heatmap-density'],
              0, 'rgba(0,0,0,0)',
              0.5, DATASET_COLORS[activeDataset],
              1, '#ffffff',
            ]
          );
        }
      } catch (err) {
        console.error('Error loading map data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (map.current.loaded()) {
      loadData();
      map.current.on('moveend', loadData);
    } else {
      map.current.on('load', () => {
        loadData();
        map.current.on('moveend', loadData);
      });
    }

    return () => {
      map.current?.off('moveend', loadData);
    };
  }, [activeDataset]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />

      {/* Dataset selector */}
      <div style={{
        position: 'absolute',
        top: 16,
        left: 16,
        background: 'rgba(0,0,0,0.8)',
        borderRadius: 8,
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        zIndex: 1,
      }}>
        {DATASETS.map(dataset => (
          <button
            key={dataset}
            onClick={() => setActiveDataset(dataset)}
            style={{
              background: activeDataset === dataset ? DATASET_COLORS[dataset] : 'transparent',
              color: '#fff',
              border: `1px solid ${DATASET_COLORS[dataset]}`,
              borderRadius: 4,
              padding: '6px 12px',
              cursor: 'pointer',
              fontSize: 12,
              textTransform: 'capitalize',
            }}
          >
            {dataset.replace('_', ' ')}
          </button>
        ))}
      </div>

      {loading && (
        <div style={{
          position: 'absolute',
          bottom: 16,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(0,0,0,0.8)',
          color: '#fff',
          padding: '8px 16px',
          borderRadius: 4,
          fontSize: 12,
        }}>
          Loading data...
        </div>
      )}
    </div>
  );
}