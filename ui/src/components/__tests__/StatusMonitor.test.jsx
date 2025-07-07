import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import StatusMonitor from '../StatusMonitor';

// Mock fetch globally
global.fetch = jest.fn();

// Mock timer functions
jest.useFakeTimers();

const mockStatus = (state, context = {}, error_message = null) => ({
  state,
  context,
  error_message
});

describe('StatusMonitor', () => {
  beforeEach(() => {
    fetch.mockClear();
    jest.clearAllMocks();
  });

  it('shows loading state initially', () => {
    render(<StatusMonitor jobId="123" />);
    expect(screen.getByText('Checking status...')).toBeInTheDocument();
  });

  it('handles successful status fetch', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus('PROCESSING'))
    });

    render(<StatusMonitor jobId="123" />);

    await waitFor(() => {
      expect(screen.getByText('Project Status: PROCESSING')).toBeInTheDocument();
    });
  });

  it('handles error state', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<StatusMonitor jobId="123" />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('calls onStateChange when state changes', async () => {
    const onStateChange = jest.fn();
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus('PROCESSING'))
    });

    render(<StatusMonitor jobId="123" onStateChange={onStateChange} />);

    await waitFor(() => {
      expect(onStateChange).toHaveBeenCalledWith('PROCESSING');
    });
  });

  it('calls onComplete when job completes', async () => {
    const onComplete = jest.fn();
    const completedStatus = mockStatus('COMPLETED', {
      retrospection_result: {
        summary: 'Test summary',
        key_decisions: ['Decision 1']
      }
    });

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(completedStatus)
    });

    render(<StatusMonitor jobId="123" onComplete={onComplete} />);

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith(completedStatus);
    });
  });

  it('calls onError when job fails', async () => {
    const onError = jest.fn();
    const errorStatus = mockStatus('ERROR', {}, 'Job failed');

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(errorStatus)
    });

    render(<StatusMonitor jobId="123" onError={onError} />);

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('Job failed');
    });
  });

  it('polls status until job completes', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockStatus('PROCESSING'))
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockStatus('COMPLETED'))
      });

    render(<StatusMonitor jobId="123" />);

    await waitFor(() => {
      expect(screen.getByText('Project Status: PROCESSING')).toBeInTheDocument();
    });

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    await waitFor(() => {
      expect(screen.getByText('Project Status: COMPLETED')).toBeInTheDocument();
    });
  });

  it('renders ingestion state correctly', async () => {
    const ingestionStatus = mockStatus('INGESTION', {
      ingested_files: [
        { destination: 'file1.txt' },
        { destination: 'file2.txt' }
      ]
    });

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(ingestionStatus)
    });

    render(<StatusMonitor jobId="123" />);

    await waitFor(() => {
      expect(screen.getByText('Processing Input Files')).toBeInTheDocument();
      expect(screen.getByText('Processing: file1.txt')).toBeInTheDocument();
      expect(screen.getByText('Processing: file2.txt')).toBeInTheDocument();
    });
  });

  it('renders idea selection state correctly', async () => {
    const ideaStatus = mockStatus('IDEA_SELECTION', {
      generated_ideas: [
        { title: 'Idea 1', description: 'Description 1' },
        { title: 'Idea 2', description: 'Description 2' }
      ]
    });

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(ideaStatus)
    });

    render(<StatusMonitor jobId="123" />);

    await waitFor(() => {
      expect(screen.getByText('Generated Ideas')).toBeInTheDocument();
      expect(screen.getByText('Idea 1')).toBeInTheDocument();
      expect(screen.getByText('Description 1')).toBeInTheDocument();
    });
  });

  it('renders design selection state correctly', async () => {
    const designStatus = mockStatus('DESIGN_SELECTION', {
      evaluated_designs: [
        {
          name: 'Design 1',
          description: 'Description 1',
          maintainability_score: 8,
          scalability_score: 9,
          reliability_score: 7
        }
      ]
    });

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(designStatus)
    });

    render(<StatusMonitor jobId="123" />);

    await waitFor(() => {
      expect(screen.getByText('Design Options')).toBeInTheDocument();
      expect(screen.getByText('Design 1')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();
      expect(screen.getByText('Maintainability')).toBeInTheDocument();
    });
  });

  it('handles network errors gracefully', async () => {
    fetch.mockImplementationOnce(() => Promise.reject(new Error('Network error')));

    render(<StatusMonitor jobId="123" />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
  });

  it('cleans up polling on unmount', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockStatus('PROCESSING'))
    });

    const { unmount } = render(<StatusMonitor jobId="123" />);

    await waitFor(() => {
      expect(screen.getByText('Project Status: PROCESSING')).toBeInTheDocument();
    });

    unmount();

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    expect(fetch).toHaveBeenCalledTimes(1);
  });
});