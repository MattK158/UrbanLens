import { useState, useEffect } from 'react';
import { getNeighborhoods } from '../api/client';

export const useNeighborhoods = () => {
  const [neighborhoods, setNeighborhoods] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getNeighborhoods()
      .then(data => {
        setNeighborhoods(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return { neighborhoods, loading, error };
};