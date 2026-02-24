import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
});

export const getNeighborhoods = async () => {
  const response = await api.get('/api/v1/neighborhoods');
  return response.data;
};

export const getNeighborhood = async (slug) => {
  const response = await api.get(`/api/v1/neighborhoods/${slug}`);
  return response.data;
};

export const compareNeighborhoods = async (slug1, slug2) => {
  const response = await api.get(`/api/v1/neighborhoods/${slug1}/compare/${slug2}`);
  return response.data;
};

export const getMapData = async (dataset, params = {}) => {
  const response = await api.get(`/api/v1/map/${dataset}`, { params });
  return response.data;
};

export const getTrends = async (dataset, neighborhood, months = 12) => {
  const response = await api.get(`/api/v1/trends/${dataset}`, {
    params: { neighborhood, months }
  });
  return response.data;
};

export const getScores = async () => {
  const response = await api.get('/api/v1/scores');
  return response.data;
};