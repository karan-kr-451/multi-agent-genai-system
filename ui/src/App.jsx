import { useState, useEffect } from 'react';
import './App.css';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';

function App() {
  const [prompt, setPrompt] = useState('Build a social media app.');
  const [githubUrl, setGithubUrl] = useState('');
  const [pdfPath, setPdfPath] = useState('');
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [localFiles, setLocalFiles] = useState([{ source_path: '', destination_filename: '' }]);
  const [pollInterval, setPollInterval] = useState(null);

  const handleAddLocalFile = () => {
    setLocalFiles([...localFiles, { source_path: '', destination_filename: '' }]);
  };

  const handleLocalFileChange = (index, field, value) => {
    const newLocalFiles = [...localFiles];
    newLocalFiles[index][field] = value;
    setLocalFiles(newLocalFiles);
  };

  const handleStartProject = async () => {
    try {
      setLoading(true);
      setError(null);
      setJobId(null);
      setStatus(null);
      
      const filesToIngest = localFiles.filter(f => f.source_path && f.destination_filename);
      
      const requestBody = {
        prompt: prompt,
        github_url: githubUrl || null,
        pdf_path: pdfPath || null,
        files_to_ingest: filesToIngest,
      };

      const response = await fetch('http://localhost:8000/start_project', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start project');
      }

      const data = await response.json();
      setJobId(data.job_id);
    } catch (error) {
      setError(error.message || 'An error occurred while starting the project');
      setLoading(false);
    }
  };

  const handleSelectIdea = async (index) => {
    if (!jobId) return;
    try {
      setError(null);
      const response = await fetch(`http://localhost:8000/jobs/${jobId}/select_idea?idea_index=${index}`, { 
        method: 'POST' 
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to select idea');
      }
    } catch (error) {
      setError(error.message || 'An error occurred while selecting the idea');
    }
  };

  const handleSelectDesign = async (index) => {
    if (!jobId) return;
    try {
      setError(null);
      const response = await fetch(`http://localhost:8000/jobs/${jobId}/select_design?design_index=${index}`, { 
        method: 'POST' 
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to select design');
      }
    } catch (error) {
      setError(error.message || 'An error occurred while selecting the design');
    }
  };

  const handleApprove = async () => {
    if (!jobId) return;
    try {
      setError(null);
      const response = await fetch(`http://localhost:8000/jobs/${jobId}/approve`, { 
        method: 'POST' 
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to approve job');
      }
    } catch (error) {
      setError(error.message || 'An error occurred while approving the job');
    }
  };

  const handleSubmitFeedback = async () => {
    if (!jobId || !feedback) return;
    try {
      setError(null);
      const response = await fetch(`http://localhost:8000/jobs/${jobId}/feedback?feedback=${encodeURIComponent(feedback)}`, { 
        method: 'POST' 
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit feedback');
      }
      
      setFeedback(''); // Clear feedback after successful submission
    } catch (error) {
      setError(error.message || 'An error occurred while submitting feedback');
    }
  };

  const handleRetry = () => {
    setError(null);
    if (jobId) {
      pollStatus(); // Retry polling if we have a jobId
    }
  };

  const pollStatus = async () => {
    try {
      const response = await fetch(`http://localhost:8000/status/${jobId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch status');
      }
      
      const data = await response.json();
      setStatus(data);
      
      if (data.state === 'COMPLETED' || data.state === 'ERROR') {
        setLoading(false);
        clearInterval(pollInterval);
        setPollInterval(null);
      }
    } catch (error) {
      setError('Lost connection to server. Click "Try Again" to resume.');
      clearInterval(pollInterval);
      setPollInterval(null);
    }
  };

  useEffect(() => {
    if (jobId && !pollInterval) {
      // Start polling when we get a jobId
      const interval = setInterval(pollStatus, 2000);
      setPollInterval(interval);
    }
    
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [jobId]);

  const renderStatusContent = () => {
    if (error) {
      return <ErrorMessage error={error} onRetry={handleRetry} />;
    }

    if (!status) {
      return loading && <LoadingSpinner message="Initializing project..." />;
    }

    return (
      <div className="status-container">
        <h2>Project Status</h2>
        <p><strong>State:</strong> {status.state}</p>

        {status.state === 'INGESTION' && status.context.ingested_files && (
          <div className="ingestion-section">
            <h3>File Ingestion Report:</h3>
            {status.context.ingested_files.map((file, index) => (
              <p key={index}>Copied <strong>{file.source}</strong> to <strong>{file.destination}</strong>: {file.result}</p>
            ))}
          </div>
        )}
        
        {status.state === 'IDEA_SELECTION' && status.context.generated_ideas && (
          <div className="idea-selection-section">
            <h3>Generated Ideas:</h3>
            {status.context.generated_ideas.map((idea, index) => (
              <div key={index} className="idea-card">
                <h4>{idea.title}</h4>
                <p>{idea.description}</p>
                <p><strong>Features:</strong> {idea.features.join(', ')}</p>
                <p><strong>Technologies:</strong> {idea.technologies.join(', ')}</p>
                <button onClick={() => handleSelectIdea(index)}>Select This Idea</button>
              </div>
            ))}
          </div>
        )}

        {status.state === 'ARCHITECT_ANALYSIS' && (
          <div className="analysis-section">
            <p><strong>Architect's Analysis:</strong> {status.context.architect_result ? JSON.stringify(status.context.architect_result) : 'Analyzing...'}</p>
            {status.context.modification_report && (
              <div className="modification-report">
                <h3>System Modification Report:</h3>
                <pre>{status.context.modification_report}</pre>
              </div>
            )}
          </div>
        )}

        {status.state === 'ANALYZING' && status.context.analyzer_result && (
          <div className="analysis-section">
            <h3>Analyzer Report:</h3>
            <p><strong>Summary:</strong> {status.context.analyzer_result.summary}</p>
            <p><strong>Domain Insights:</strong> {status.context.analyzer_result.domain_insights}</p>
            <p><strong>Innovative Suggestions:</strong></p>
            <ul>
              {status.context.analyzer_result.innovative_suggestions?.map((s, i) => (
                <li key={i}>{s.suggestion} - {s.justification}</li>
              ))}
            </ul>
            <p><strong>Reasoning:</strong> {status.context.analyzer_result.reasoning_explanation}</p>
          </div>
        )}

        {status.state === 'DESIGN_SELECTION' && status.context.evaluated_designs && (
          <div className="design-selection-section">
            <h3>Evaluated Designs:</h3>
            {status.context.evaluated_designs.map((design, index) => (
              <div key={index} className="design-card">
                <h4>Design Option {index + 1}</h4>
                <p><strong>Frontend:</strong> {design.architecture.frontend.description}</p>
                <p><strong>Backend:</strong> {design.architecture.backend.description}</p>
                <p><strong>Database:</strong> {design.architecture.database_schema ? JSON.stringify(design.architecture.database_schema) : 'N/A'}</p>
                {design.diagram_url && <p><strong>Diagram:</strong> <a href={design.diagram_url} target="_blank" rel="noopener noreferrer">View Diagram</a></p>}
                {design.evaluation && (
                  <div className="evaluation-scores">
                    <p>Cost: {design.evaluation.cost_score}/10, Complexity: {design.evaluation.complexity_score}/10, Scalability: {design.evaluation.scalability_score}/10</p>
                    <p>Pros: {design.evaluation.pros.join(', ')}</p>
                    <p>Cons: {design.evaluation.cons.join(', ')}</p>
                  </div>
                )}
                <button onClick={() => handleSelectDesign(index)}>Select This Design</button>
              </div>
            ))}
          </div>
        )}

        {status.state === 'STATIC_ANALYSIS' && (
          <div className="analysis-section">
            <h3>Static Analysis:</h3>
            <p><strong>Issues Found:</strong> {status.context.sentinel_report?.issues_found ? 'Yes' : 'No'}</p>
            {status.context.sentinel_report?.summary && <p><strong>Summary:</strong> {status.context.sentinel_report.summary}</p>}
            {status.context.sentinel_report?.report && <pre>{status.context.sentinel_report.report}</pre>}
          </div>
        )}

        {status.state === 'REFACTORING' && (
          <div className="refactoring-section">
            <h3>Refactoring:</h3>
            <p><strong>Status:</strong> {status.context.refactoring_result?.status}</p>
            <p><strong>Message:</strong> {status.context.refactoring_result?.message}</p>
            {status.context.refactoring_result?.changes_made && (
              <p><strong>Changes Made:</strong> {status.context.refactoring_result.changes_made.join(', ')}</p>
            )}
          </div>
        )}

        {status.state === 'INFRASTRUCTURE_GENERATION' && status.context.infrastructure_result && (
          <div className="infrastructure-section">
            <h3>Infrastructure Generation:</h3>
            <p><strong>Explanation:</strong> {status.context.infrastructure_result.explanation}</p>
            <pre>{status.context.infrastructure_result.iac_code}</pre>
          </div>
        )}

        {status.state === 'DEPLOYING' && (
          <div className="deployment-section">
            <h3>Deployment:</h3>
            <p><strong>Status:</strong> {status.context.deployment_result?.status}</p>
            <p><strong>Message:</strong> {status.context.deployment_result?.message}</p>
            {status.context.deployment_result?.deployment_url && (
              <p><strong>URL:</strong> <a href={status.context.deployment_result.deployment_url} target="_blank" rel="noopener noreferrer">{status.context.deployment_result.deployment_url}</a></p>
            )}
          </div>
        )}

        {status.state === 'MONITORING' && (
          <div className="monitoring-section">
            <h3>Monitoring:</h3>
            <p><strong>Overall Health:</strong> {status.context.monitor_report?.overall_health}</p>
            {status.context.monitor_report?.performance_issues?.length > 0 && (
              <p><strong>Performance Issues:</strong> {JSON.stringify(status.context.monitor_report.performance_issues)}</p>
            )}
            {status.context.monitor_report?.errors_detected?.length > 0 && (
              <p><strong>Errors Detected:</strong> {JSON.stringify(status.context.monitor_report.errors_detected)}</p>
            )}
            {status.context.monitor_report?.security_alerts?.length > 0 && (
              <p><strong>Security Alerts:</strong> {JSON.stringify(status.context.monitor_report.security_alerts)}</p>
            )}
          </div>
        )}

        {status.state === 'PENDING_APPROVAL' && (
          <div className="approval-section">
            <h3>Approval Required</h3>
            <p>The Designer Agent has created a plan. Please review and approve.</p>
            <pre>{JSON.stringify(status.context.selected_design, null, 2)}</pre>
            <button onClick={() => handleApprove()}>Approve Plan</button>
          </div>
        )}

        {status.state === 'COMPLETED' && (
          <div className="completed-section">
            <h3>Project Complete!</h3>
            <p>All agents have finished their tasks.</p>
            {status.context.retrospection_result && (
              <div className="retrospection-report">
                <h4>Retrospection Report:</h4>
                <p><strong>Outcome:</strong> {status.context.retrospection_result.job_outcome}</p>
                {status.context.retrospection_result.failure_reason && <p><strong>Reason:</strong> {status.context.retrospection_result.failure_reason}</p>}
                <p><strong>Insights:</strong> {status.context.retrospection_result.insights}</p>
                {status.context.retrospection_result.agent_specific_feedback && (
                  <div>
                    <h5>Agent Feedback:</h5>
                    <pre>{JSON.stringify(status.context.retrospection_result.agent_specific_feedback, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
            {status.context.optimized_prompts_result && (
              <div className="prompt-optimization-report">
                <h4>Prompt Optimization Report:</h4>
                <p><strong>Explanation:</strong> {status.context.optimized_prompts_result.explanation}</p>
                <pre>{JSON.stringify(status.context.optimized_prompts_result.optimized_prompts, null, 2)}</pre>
              </div>
            )}
          </div>
        )}

        {status.state === 'ERROR' && (
          <div className="error-section">
            <h3>Error!</h3>
            <p>{status.error_message}</p>
            {status.context.retrospection_result && (
              <div className="retrospection-report">
                <h4>Retrospection Report:</h4>
                <p><strong>Outcome:</strong> {status.context.retrospection_result.job_outcome}</p>
                {status.context.retrospection_result.failure_reason && <p><strong>Reason:</strong> {status.context.retrospection_result.failure_reason}</p>}
                <p><strong>Insights:</strong> {status.context.retrospection_result.insights}</p>
                {status.context.retrospection_result.agent_specific_feedback && (
                  <div>
                    <h5>Agent Feedback:</h5>
                    <pre>{JSON.stringify(status.context.retrospection_result.agent_specific_feedback, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
            {status.context.optimized_prompts_result && (
              <div className="prompt-optimization-report">
                <h4>Prompt Optimization Report:</h4>
                <p><strong>Explanation:</strong> {status.context.optimized_prompts_result.explanation}</p>
                <pre>{JSON.stringify(status.context.optimized_prompts_result.optimized_prompts, null, 2)}</pre>
              </div>
            )}
          </div>
        )}

        {(status.state === 'PENDING_APPROVAL' || status.state === 'ERROR') && (
          <div className="feedback-section">
            <h3>Provide Feedback:</h3>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="e.g., 'Make the UI more minimalist', 'Fix the database schema for users table'"
            />
            <button onClick={handleSubmitFeedback} disabled={!feedback}>
              Submit Feedback
            </button>
          </div>
        )}

        {loading && (
          <div className="status-overlay">
            <LoadingSpinner message={`Processing ${status.state.toLowerCase()}...`} />
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Multi-Agent GenAI Project Builder v13</h1>
        <div className="input-container">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter a high-level project concept..."
          />
          
          <div className="optional-inputs-section">
            <h3>Optional Inputs:</h3>
            <input
              type="text"
              placeholder="GitHub Repository URL (e.g., https://github.com/user/repo)"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
            />
            <input
              type="text"
              placeholder="Absolute Path to PDF Spec (e.g., /home/user/spec.pdf)"
              value={pdfPath}
              onChange={(e) => setPdfPath(e.target.value)}
            />
          </div>

          <div className="local-files-section">
            <h3>Local Files to Ingest:</h3>
            {localFiles.map((file, index) => (
              <div key={index} className="file-input-row">
                <input
                  type="text"
                  placeholder="Absolute Path (e.g., /home/user/data.csv)"
                  value={file.source_path}
                  onChange={(e) => handleLocalFileChange(index, 'source_path', e.target.value)}
                />
                <input
                  type="text"
                  placeholder="Filename in Workspace (e.g., my_data.csv)"
                  value={file.destination_filename}
                  onChange={(e) => handleLocalFileChange(index, 'destination_filename', e.target.value)}
                />
              </div>
            ))}
            <button onClick={handleAddLocalFile}>Add Another File</button>
          </div>

          <button 
            onClick={handleStartProject} 
            disabled={loading || !prompt}
            className={loading ? 'disabled' : ''}
          >
            {loading ? 'Building...' : 'Start Project'}
          </button>
        </div>

        {jobId && <p>Job ID: {jobId}</p>}
        {renderStatusContent()}
      </header>
    </div>
  );
}

export default App;
