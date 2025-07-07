import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';

const StatusMonitor = ({ jobId, onStateChange, onComplete, onError }) => {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`/api/status/${jobId}`, {
        headers: {
          'X-API-Key': process.env.REACT_APP_API_KEY
        }
      });
      
      if (!response.ok) {
        throw new Error(`Status check failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      setStatus(data);
      setLoading(false);
      
      if (onStateChange) {
        onStateChange(data.state);
      }
      
      if (data.state === 'COMPLETED') {
        if (onComplete) {
          onComplete(data);
        }
      } else if (data.state === 'ERROR') {
        if (onError) {
          onError(data.error_message || 'An unknown error occurred');
        }
      }
      
      return data.state;
    } catch (err) {
      setError(err.message);
      setLoading(false);
      if (onError) {
        onError(err.message);
      }
      return 'ERROR';
    }
  }, [jobId, onStateChange, onComplete, onError]);

  useEffect(() => {
    const pollStatus = async () => {
      const state = await fetchStatus();
      
      // Continue polling if job is not in a terminal state
      if (!['COMPLETED', 'ERROR'].includes(state)) {
        setTimeout(pollStatus, 5000); // Poll every 5 seconds
      }
    };

    pollStatus();
    
    return () => {
      // Clean up any pending timeouts
      clearTimeout(pollStatus);
    };
  }, [fetchStatus]);

  const renderStateSpecificContent = () => {
    if (!status) return null;

    switch (status.state) {
      case 'INGESTION':
        return (
          <div className="ingestion-section">
            <h3>Processing Input Files</h3>
            {status.context?.ingested_files?.map((file, index) => (
              <div key={index} className="file-status">
                <p>Processing: {file.destination}</p>
              </div>
            ))}
          </div>
        );

      case 'IDEA_SELECTION':
        return (
          <div className="idea-selection-section">
            <h3>Generated Ideas</h3>
            {status.context?.generated_ideas?.map((idea, index) => (
              <div key={index} className="idea-card">
                <h4>{idea.title}</h4>
                <p>{idea.description}</p>
              </div>
            ))}
          </div>
        );

      case 'DESIGN_SELECTION':
        return (
          <div className="design-selection-section">
            <h3>Design Options</h3>
            {status.context?.evaluated_designs?.map((design, index) => (
              <div key={index} className="design-card">
                <h4>{design.name}</h4>
                <div className="evaluation-scores">
                  <div className="score-item">
                    <div className="score-value">{design.maintainability_score}</div>
                    <div className="score-label">Maintainability</div>
                  </div>
                  <div className="score-item">
                    <div className="score-value">{design.scalability_score}</div>
                    <div className="score-label">Scalability</div>
                  </div>
                  <div className="score-item">
                    <div className="score-value">{design.reliability_score}</div>
                    <div className="score-label">Reliability</div>
                  </div>
                </div>
                <p>{design.description}</p>
              </div>
            ))}
          </div>
        );

      case 'PENDING_APPROVAL':
        return (
          <div className="approval-section">
            <h3>Ready for Review</h3>
            <p>The selected design is ready for your approval.</p>
            {status.context?.selected_design && (
              <div className="selected-design">
                <h4>{status.context.selected_design.name}</h4>
                <p>{status.context.selected_design.description}</p>
              </div>
            )}
          </div>
        );

      case 'COMPLETED':
        return (
          <div className="completed-section">
            <h3>Project Generation Complete</h3>
            {status.context?.retrospection_result && (
              <div className="retrospection-report">
                <h4>Project Summary</h4>
                <p>{status.context.retrospection_result.summary}</p>
                <h4>Key Decisions</h4>
                <ul>
                  {status.context.retrospection_result.key_decisions.map((decision, index) => (
                    <li key={index}>{decision}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );

      case 'ERROR':
        return (
          <div className="error-section">
            <ErrorMessage 
              error={status.error_message || 'An unknown error occurred'} 
              onRetry={() => fetchStatus()}
            />
          </div>
        );

      default:
        return (
          <div className={`${status.state.toLowerCase()}-section`}>
            <h3>Processing: {status.state}</h3>
            <p>Please wait while we process your request...</p>
          </div>
        );
    }
  };

  if (loading) {
    return <LoadingSpinner message="Checking status..." />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={() => fetchStatus()} />;
  }

  return (
    <div className="status-container">
      <h2>Project Status: {status?.state}</h2>
      {renderStateSpecificContent()}
    </div>
  );
};

StatusMonitor.propTypes = {
  jobId: PropTypes.string.isRequired,
  onStateChange: PropTypes.func,
  onComplete: PropTypes.func,
  onError: PropTypes.func
};

export default StatusMonitor;