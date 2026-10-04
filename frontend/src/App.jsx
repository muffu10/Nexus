import { useEffect, useState } from "react";

import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  useNavigate,
  useParams,
  Navigate,
} from "react-router-dom";

import NewConnection from "./NewConnection";
import Register from "./Register";

import Login from "./login";

import {
  LayoutDashboard,
  Database,
  Settings,
  RefreshCw,
  Plus,
  ArrowRight,
  Server,
  CheckCircle2,
  AlertCircle,
  LogOut,
} from "lucide-react";

import {
  getConnections,
  getConnectionSchema,
  getConnectionSamples,
  getMappingSuggestions,
  approveMapping,
  runSync,
  getSyncHistory,
} from "./api/connections";

import "./App.css";


/* =========================================================
   SIDEBAR
========================================================= */

function Sidebar() {
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem("datasync_token");

    navigate("/login", {
      replace: true,
    });
  }

  return (
    <aside className="sidebar">

      <div className="brand">

        <div className="brand-icon">
          <RefreshCw size={22} />
        </div>

        <div>
          <h2>DataSync</h2>
          <span>Integration Platform</span>
        </div>

      </div>


      <nav className="navigation">

        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }
        >
          <LayoutDashboard size={19} />
          Dashboard
        </NavLink>


        <NavLink
          to="/connections"
          className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }
        >
          <Database size={19} />
          Connections
        </NavLink>


        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }
        >
          <Settings size={19} />
          Settings
        </NavLink>

      </nav>


      <div className="sidebar-footer">

        <div className="system-status">

          <span className="status-dot"></span>

          <div>
            <strong>System Online</strong>
            <span>All services operational</span>
          </div>

        </div>


        <button
          type="button"
          onClick={handleLogout}
          className="logout-button"
        >
          <LogOut size={18} />
          Logout
        </button>

      </div>

    </aside>
  );
}


/* =========================================================
   DASHBOARD
========================================================= */

function Dashboard() {

  const navigate = useNavigate();

  return (
    <>

      <header className="page-header">

        <div>

          <h1>Dashboard</h1>

          <p>
            Monitor your data synchronization activity.
          </p>

        </div>


        <button
          className="primary-button"
          onClick={() =>
            navigate("/connections/new")
          }
        >
          <Plus size={16} />
          New Connection
        </button>

      </header>


      <section className="stats-grid">

        <div className="stat-card">

          <span className="stat-label">
            Total Connections
          </span>

          <strong className="stat-value">
            —
          </strong>

          <span className="stat-description">
            Configured integrations
          </span>

        </div>


        <div className="stat-card">

          <span className="stat-label">
            Successful Syncs
          </span>

          <strong className="stat-value">
            —
          </strong>

          <span className="stat-description">
            Completed successfully
          </span>

        </div>


        <div className="stat-card">

          <span className="stat-label">
            Sync Warnings
          </span>

          <strong className="stat-value">
            —
          </strong>

          <span className="stat-description">
            Completed with errors
          </span>

        </div>


        <div className="stat-card">

          <span className="stat-label">
            Failed Syncs
          </span>

          <strong className="stat-value">
            —
          </strong>

          <span className="stat-description">
            Requires attention
          </span>

        </div>

      </section>


      <section className="content-card">

        <div className="card-header">

          <div>

            <h2>Recent Sync Runs</h2>

            <p>
              Latest synchronization activity across
              your connections.
            </p>

          </div>


          <button
            className="secondary-button"
            onClick={() =>
              navigate("/connections")
            }
          >
            View connections
          </button>

        </div>


        <div className="empty-state">

          <RefreshCw size={30} />

          <h3>
            Sync activity will appear here
          </h3>

          <p>
            Your synchronization history will be
            displayed on the dashboard.
          </p>

        </div>

      </section>

    </>
  );
}


/* =========================================================
   CONNECTIONS
========================================================= */

function Connections() {

  const navigate = useNavigate();

  const [
    connections,
    setConnections,
  ] = useState([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState(null);


  useEffect(() => {

    async function loadConnections() {

      try {

        setLoading(true);

        const data =
          await getConnections();

        setConnections(data);

      } catch (err) {

        console.error(err);

        setError(
          "Unable to load connections from the server."
        );

      } finally {

        setLoading(false);

      }

    }

    loadConnections();

  }, []);


  return (
    <>

      <header className="page-header">

        <div>

          <h1>Connections</h1>

          <p>
            Configure and manage your data sources.
          </p>

        </div>


        <button 
            className="primary-button"
            onClick={() => navigate("/connections/new")}
          >

          <Plus size={16} />

          New Connection

        </button>

      </header>


      {loading && (

        <div className="content-card">

          <div className="loading-state">

            <RefreshCw
              size={24}
              className="spin"
            />

            <span>
              Loading connections...
            </span>

          </div>

        </div>

      )}


      {error && (

        <div className="error-banner">

          <AlertCircle size={18} />

          <span>{error}</span>

        </div>

      )}


      {!loading &&
        !error &&
        connections.length === 0 && (

          <div className="content-card">

            <div className="empty-state">

              <Database size={32} />

              <h3>
                No connections yet
              </h3>

              <p>
                Create your first connection to start
                synchronizing data.
              </p>

            </div>

          </div>

        )}


      {!loading &&
        !error &&
        connections.length > 0 && (

          <div className="connections-list">

            {connections.map(
              (connection) => (

                <div
                  className="connection-card"
                  key={connection.id}
                >

                  <div className="connection-main">

                    <div className="connection-icon">
                      <Database size={20} />
                    </div>


                    <div className="connection-info">

                      <div className="connection-title">

                        <h2>
                          {connection.name}
                        </h2>

                        <span className="connection-status">
                          <CheckCircle2 size={13} />
                          Active
                        </span>

                      </div>


                      <span className="connection-id">
                        Connection #
                        {connection.connection_number}
                      </span>

                    </div>

                  </div>


                  <div className="connection-flow">

                    <div className="database-endpoint">

                      <span>
                        Source
                      </span>

                      <strong>
                        {connection.source_type}
                      </strong>

                      <small>
                        {connection.source_table}
                      </small>

                    </div>


                    <ArrowRight
                      size={20}
                      className="flow-arrow"
                    />


                    <div className="database-endpoint">

                      <span>
                        Destination
                      </span>

                      <strong>
                        {connection.destination_type}
                      </strong>

                      <small>
                        {connection.destination_table}
                      </small>

                    </div>

                  </div>


                  <button
                    className="view-button"
                    onClick={() =>
                      navigate(
                        `/connections/${connection.id}`
                      )
                    }
                  >
                    View
                    <ArrowRight size={15} />
                  </button>

                </div>

              )
            )}

          </div>

        )}

    </>
  );
}


/* =========================================================
   CONNECTION DETAILS
========================================================= */

function ConnectionDetails() {

  const {
    connectionId,
  } = useParams();

  const [
    activeTab,
    setActiveTab,
  ] = useState("schema");

  const [
    schema,
    setSchema,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState(null);


useEffect(() => {

 async function loadSchema() {
  try {
    setLoading(true);
    setError(null);

    const schemaData =
      await getConnectionSchema(connectionId);

    setSchema(schemaData);

  } catch (err) {

    console.error(err);

    setError(
      "Unable to load the connection schema."
    );

  } finally {

    setLoading(false);
  }
}

  loadSchema();

}, [connectionId]);


  return (
    <>

      <header className="page-header">

        <div>

          <div className="breadcrumb">
            Connections /
            Connection #{connectionId}
          </div>

          <h1>
            Connection #{connectionId}
          </h1>

          <p>
            Review and manage this data integration.
          </p>

        </div>

      </header>


      <div className="detail-tabs">

        <button
          className={`detail-tab ${
            activeTab === "schema"
              ? "active"
              : ""
          }`}
          onClick={() =>
            setActiveTab("schema")
          }
        >
          Schema
        </button>


        <button
          className={`detail-tab ${
            activeTab === "mapping"
              ? "active"
              : ""
          }`}
          onClick={() =>
            setActiveTab("mapping")
          }
        >
          Mapping
        </button>


        <button
          className={`detail-tab ${
            activeTab === "sync"
              ? "active"
              : ""
          }`}
          onClick={() =>
            setActiveTab("sync")
          }
        >
          Sync
        </button>


        <button
          className={`detail-tab ${
            activeTab === "history"
              ? "active"
              : ""
          }`}
          onClick={() =>
            setActiveTab("history")
          }
        >
          History
        </button>

      </div>


      {activeTab === "schema" && (

        <>

          {loading && (

            <div className="content-card">

              <div className="loading-state">

                <RefreshCw
                  size={24}
                  className="spin"
                />

                <span>
                  Loading database schema...
                </span>

              </div>

            </div>

          )}


          {error && (

            <div className="error-banner">

              <AlertCircle size={18} />

              <span>{error}</span>

            </div>

          )}


          {!loading &&
            !error &&
            schema && (

              <SchemaViewer
                schema={schema}
              />

            )}

        </>

      )}


      {activeTab === "mapping" && (

        <MappingViewer
          connectionId={connectionId}
        />

      )}


      {activeTab === "sync" && (<SyncViewer connectionId={connectionId} />)}


      {activeTab === "history" && (<SyncHistoryViewer connectionId={connectionId} />)}

    </>
  );
}


/* =========================================================
   SYNC VIEWER
========================================================= */

function SyncViewer({ connectionId }) {
  const [syncing, setSyncing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSync() {
    try {
      setSyncing(true);
      setResult(null);
      setError(null);

      const data = await runSync(connectionId);

      setResult(data);
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to run synchronization."
      );
    } finally {
      setSyncing(false);
    }
  }

  const status = result?.status;

  const inserted = result?.inserted_count ?? 0;
  const updated = result?.updated_count ?? 0;
  const failed = result?.failed_count ?? 0;

  return (
    <div className="sync-section">

      <div className="content-card">

        <div className="card-header">

          <div>
            <h2>Run Synchronization</h2>

            <p>
              Synchronize approved mappings from the source
              database to the destination.
            </p>
          </div>

          <button
            className="primary-button"
            onClick={handleSync}
            disabled={syncing}
          >
            <RefreshCw
              size={15}
              className={syncing ? "spin" : ""}
            />

            {syncing
              ? "Synchronizing..."
              : "Run Sync"}
          </button>

        </div>


        <div className="sync-info">

          <div className="sync-info-icon">
            <AlertCircle size={17} />
          </div>

          <div>
            <strong>Before running a sync</strong>

            <p>
              Make sure the required field mappings have
              been approved.
            </p>
          </div>

        </div>

      </div>


      {error && (
        <div className="error-banner">

          <AlertCircle size={18} />

          <span>{error}</span>

        </div>
      )}


      {result && (
        <div className="content-card sync-result-card">

          <div className="card-header">

            <div>

              <h2>
                {status === "success"
                  ? "Synchronization completed"
                  : status === "completed_with_errors"
                    ? "Synchronization completed with errors"
                    : "Synchronization failed"}
              </h2>

              <p>
                Sync run #{result.id ?? "—"}
              </p>

            </div>

            <span
              className={`match-badge ${
                status === "success"
                  ? "high"
                  : ""
              }`}
            >
              {status || "unknown"}
            </span>

          </div>


          <div className="sync-metrics">

            <div className="stat-card">

              <span className="stat-label">
                Inserted
              </span>

              <strong className="stat-value">
                {inserted}
              </strong>

            </div>


            <div className="stat-card">

              <span className="stat-label">
                Updated
              </span>

              <strong className="stat-value">
                {updated}
              </strong>

            </div>


            <div className="stat-card">

              <span className="stat-label">
                Failed
              </span>

              <strong className="stat-value">
                {failed}
              </strong>

            </div>

          </div>


          {result.error_message && (
            <div className="error-banner">

              <AlertCircle size={18} />

              <span>
                {result.error_message}
              </span>

            </div>
          )}

        </div>
      )}

    </div>
  );
}


/* =========================================================
   SYNC HISTORY VIEWER
========================================================= */

function SyncHistoryViewer({ connectionId }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadHistory() {
      try {
        setLoading(true);
        setError(null);

        const data = await getSyncHistory(connectionId);

        setHistory(
          Array.isArray(data)
            ? data
            : data.sync_runs || []
        );
      } catch (err) {
        console.error(err);

        setError(
          err.response?.data?.detail ||
            "Unable to load synchronization history."
        );
      } finally {
        setLoading(false);
      }
    }

    loadHistory();
  }, [connectionId]);

  function formatDate(value) {
    if (!value) {
      return "—";
    }

    return new Date(value).toLocaleString();
  }

  function getStatusClass(status) {
    if (status === "success") {
      return "success";
    }

    if (status === "completed_with_errors") {
      return "warning";
    }

    if (status === "failed") {
      return "error";
    }

    return "";
  }

  return (
    <div className="content-card">

      <div className="card-header">

        <div>
          <h2>Sync History</h2>

          <p>
            Previous synchronization runs for this connection.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={() => {
            window.location.reload();
          }}
        >
          <RefreshCw size={15} />
          Refresh
        </button>

      </div>


      {loading && (
        <div className="loading-state">

          <RefreshCw
            size={24}
            className="spin"
          />

          <span>
            Loading synchronization history...
          </span>

        </div>
      )}


      {error && (
        <div className="error-banner">

          <AlertCircle size={18} />

          <span>{error}</span>

        </div>
      )}


      {!loading && !error && history.length === 0 && (
        <div className="empty-state">

          <RefreshCw size={30} />

          <h3>
            No synchronization runs yet
          </h3>

          <p>
            Run a synchronization to see its history here.
          </p>

        </div>
      )}


      {!loading && !error && history.length > 0 && (
        <div className="sync-history-table">

          <div className="sync-history-header">
            <span>Run</span>
            <span>Status</span>
            <span>Started</span>
            <span>Inserted</span>
            <span>Updated</span>
            <span>Failed</span>
          </div>


          {history.map((run) => (

            <div
              className="sync-history-row"
              key={run.id}
            >

              <span>
                #{run.id}
              </span>


              <span>
                <span
                  className={`sync-status ${getStatusClass(
                    run.status
                  )}`}
                >
                  {run.status}
                </span>
              </span>


              <span>
                {formatDate(run.started_at)}
              </span>


              <span>
                {run.inserted_count ?? 0}
              </span>


              <span>
                {run.updated_count ?? 0}
              </span>


              <span>
                {run.failed_count ?? 0}
              </span>

            </div>

          ))}

        </div>
      )}

    </div>
  );
}



/* =========================================================
   SCHEMA VIEWER
========================================================= */

function SchemaViewer({ schema }) {
  const sourceColumns =
    schema?.source?.[schema?.source_table] || [];

  const destinationColumns =
    schema?.destination?.[schema?.destination_table] || [];

  return (
    <div className="schema-grid">
      <SchemaCard
        title="Source"
        type="PostgreSQL"
        columns={sourceColumns}
      />

      <SchemaCard
        title="Destination"
        type="PostgreSQL"
        columns={destinationColumns}
      />
    </div>
  );
}


function normalizeColumns(
  columns
) {

  if (Array.isArray(columns)) {
    return columns;
  }


  if (
    typeof columns === "object" &&
    columns !== null
  ) {

    const firstTable =
      Object.values(columns)[0];

    if (Array.isArray(firstTable)) {
      return firstTable;
    }

  }


  return [];
}


function SchemaCard({
  title,
  type,
  columns,
}) {

  return (

    <section className="content-card schema-card">

      <div className="schema-card-header">

        <div className="schema-title">

          <div className="connection-icon">
            <Database size={19} />
          </div>

          <div>

            <h2>{title}</h2>

            <span>
              {type}
            </span>

          </div>

        </div>


        <span className="column-count">
          {columns.length} columns
        </span>

      </div>


      <div className="schema-table">

        <div className="schema-table-header">

          <span>Column</span>
          <span>Type</span>
          <span>Properties</span>

        </div>


        {columns.length === 0 && (

          <div className="schema-empty">
            No columns found.
          </div>

        )}


        {columns.map(
          (column, index) => {

            const columnName =
              column.name ||
              column.column_name ||
              `Column ${index + 1}`;

            const columnType =
              column.type ||
              column.data_type ||
              "Unknown";


            return (

              <div
                className="schema-row"
                key={`${columnName}-${index}`}
              >

                <div className="schema-column-name">

                  <span className="column-icon">
                    #
                  </span>

                  <strong>
                    {columnName}
                  </strong>

                </div>


                <span className="schema-type">
                  {columnType}
                </span>


                <div className="schema-properties">

                  {column.primary_key && (
                    <span className="property-badge primary">
                      PK
                    </span>
                  )}

                  {column.unique && (
                    <span className="property-badge">
                      UNIQUE
                    </span>
                  )}

                  {column.nullable === false && (
                    <span className="property-badge">
                      NOT NULL
                    </span>
                  )}

                </div>

              </div>

            );

          }
        )}

      </div>

    </section>

  );
}


/* =========================================================
   MAPPING VIEWER
========================================================= */

function MappingViewer({
  connectionId,
}) {

  const [
    suggestions,
    setSuggestions,
  ] = useState([]);

  const [
    schema,
    setSchema,
  ] = useState(null);

  const [
    samples,
    setSamples,
  ] = useState(null);

  const [
    selectedMapping,
    setSelectedMapping,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState(null);

  const [
    approvingId,
    setApprovingId,
  ] = useState(null);


  async function loadData() {

    try {

      setLoading(true);
      setError(null);


      const [
        mappingData,
        schemaData,
        sampleData,
      ] = await Promise.all([

        getMappingSuggestions(
          connectionId
        ),

        getConnectionSchema(
          connectionId
        ),

        getConnectionSamples(
          connectionId
        ),

      ]);


      console.log(
        "Mapping API response:",
        mappingData
      );

      console.log(
        "Schema API response:",
        schemaData
      );

      console.log(
        "Samples API response:",
        sampleData
      );


      const mappings =
        Array.isArray(mappingData)
          ? mappingData
          : mappingData.mappings ||
            mappingData.suggestions ||
            mappingData.results ||
            [];


      setSuggestions(mappings);
      setSchema(schemaData);
      setSamples(sampleData);

    } catch (err) {

      console.error(err);

      setError(
        "Unable to load mapping information."
      );

    } finally {

      setLoading(false);

    }

  }


  useEffect(() => {

    loadData();

  }, [connectionId]);


  async function handleApprove(
    suggestionId
  ) {

    try {

      setApprovingId(
        suggestionId
      );


      await approveMapping(
        suggestionId
      );


      setSuggestions(
        (current) =>
          current.map(
            (suggestion) =>
              suggestion.id ===
              suggestionId
                ? {
                    ...suggestion,
                    review_status:
                      "approved",
                  }
                : suggestion
          )
      );


      setSelectedMapping(
        (current) =>
          current &&
          current.id === suggestionId
            ? {
                ...current,
                review_status:
                  "approved",
              }
            : current
      );

    } catch (err) {

      console.error(err);

      setError(
        "Unable to approve this mapping."
      );

    } finally {

      setApprovingId(null);

    }

  }


  if (loading) {

    return (

      <div className="content-card">

        <div className="loading-state">

          <RefreshCw
            size={24}
            className="spin"
          />

          <span>
            Loading mapping information...
          </span>

        </div>

      </div>

    );

  }


  return (

    <div className="mapping-section">

      <div className="mapping-header">

        <div>

          <h2>
            Field Mapping
          </h2>

          <p>
            Review the mappings suggested by the
            DataSync mapping engine.
          </p>

        </div>


        <button
          className="secondary-button"
          onClick={loadData}
        >

          <RefreshCw size={14} />

          Refresh

        </button>

      </div>


      {error && (

        <div className="error-banner">

          <AlertCircle size={18} />

          <span>{error}</span>

        </div>

      )}


      {suggestions.length === 0 &&
        !error && (

          <div className="content-card">

            <div className="empty-state">

              <Database size={32} />

              <h3>
                No mapping suggestions
              </h3>

              <p>
                There are currently no mapping
                suggestions for this connection.
              </p>

            </div>

          </div>

        )}


      {suggestions.length > 0 && (

        <div className="content-card mapping-table">

          <div className="mapping-table-header">

            <span>
              Source Field
            </span>

            <span>
              Destination Field
            </span>

            <span>
              Confidence
            </span>

            <span>
              Status
            </span>

            <span>
              Action
            </span>

          </div>


          {suggestions.map(
            (suggestion, index) => {

              const sourceField =
                suggestion.source_field ??
                suggestion.source ??
                suggestion.sourceField ??
                "Unknown";


              const destinationField =
                suggestion.destination_field ??
                suggestion.destination ??
                suggestion.destinationField ??
                "Unknown";


              const confidence =
                Number(
                  suggestion.confidence ?? 0
                );


              const confidencePercent =
                confidence <= 1
                  ? Math.round(
                      confidence * 100
                    )
                  : Math.round(
                      confidence
                    );


              const status =
                suggestion.match_status ??
                suggestion.status ??
                "pending";


              const approved =
                suggestion.review_status ===
                "approved";


              const suggestionId =
                suggestion.id ??
                suggestion.suggestion_id ??
                index;


              return (

                <div
                  className="mapping-row mapping-row-clickable"
                  key={suggestionId}
                  onClick={() =>
                    setSelectedMapping(
                      suggestion
                    )
                  }
                >

                  <div className="mapping-field">

                    <span className="mapping-field-icon">
                      S
                    </span>

                    <strong>
                      {sourceField}
                    </strong>

                  </div>


                  <div className="mapping-field">

                    <span className="mapping-field-icon destination">
                      D
                    </span>

                    <strong>
                      {destinationField}
                    </strong>

                  </div>


                  <div className="confidence-cell">

                    <div className="confidence-bar">

                      <div
                        className="confidence-fill"
                        style={{
                          width: `${Math.min(
                            confidencePercent,
                            100
                          )}%`,
                        }}
                      />

                    </div>


                    <span>
                      {confidencePercent}%
                    </span>

                  </div>


                  <div>

                    <span
                      className={`match-badge ${
                        status ===
                        "high_confidence"
                          ? "high"
                          : ""
                      }`}
                    >
                      {status}
                    </span>

                  </div>


                  <div
                    className="mapping-action"
                    onClick={(event) =>
                      event.stopPropagation()
                    }
                  >

                    {approved ? (

                      <span className="approved-badge">

                        <CheckCircle2
                          size={14}
                        />

                        Approved

                      </span>

                    ) : (

                      <button
                        className="approve-button"
                        disabled={
                          approvingId ===
                          suggestionId
                        }
                        onClick={() =>
                          handleApprove(
                            suggestionId
                          )
                        }
                      >

                        {approvingId ===
                        suggestionId
                          ? "Approving..."
                          : "Approve"}

                      </button>

                    )}

                  </div>

                </div>

              );

            }
          )}

        </div>

      )}


      {suggestions.length > 0 && (

        <p className="mapping-note">

          Click a mapping to view its details
          and supporting evidence.

        </p>

      )}


      {selectedMapping && (

        <MappingDetailsDrawer

          mapping={
            selectedMapping
          }

          schema={schema}

          samples={samples}

          onClose={() =>
            setSelectedMapping(null)
          }

          onApprove={
            handleApprove
          }

          approvingId={
            approvingId
          }

        />

      )}

    </div>

  );
}


/* =========================================================
   MAPPING DETAILS DRAWER
========================================================= */

function MappingDetailsDrawer({
  mapping,
  schema,
  samples,
  onClose,
  onApprove,
  approvingId,
}) {

  const sourceField =
    mapping.source_field ??
    mapping.source ??
    mapping.sourceField ??
    "Unknown";


  const destinationField =
    mapping.destination_field ??
    mapping.destination ??
    mapping.destinationField ??
    "Unknown";


  const confidence =
    Number(
      mapping.confidence ?? 0
    );


  const confidencePercent =
    confidence <= 1
      ? Math.round(
          confidence * 100
        )
      : Math.round(
          confidence
        );


  const status =
    mapping.match_status ??
    mapping.status ??
    "pending";


  const approved =
    mapping.review_status ===
    "approved";


  let signals =
    mapping.signals ?? {};


  if (
    typeof signals ===
    "string"
  ) {

    try {

      signals =
        JSON.parse(
          signals
        );

    } catch {

      signals = {};

    }

  }


  const sourceColumn =
    findColumn(
      schema,
      "source",
      sourceField
    );


  const destinationColumn =
    findColumn(
      schema,
      "destination",
      destinationField
    );


  const sourceSamples =
    getColumnSamples(
      samples,
      "source",
      sourceField
    );


  const destinationSamples =
    getColumnSamples(
      samples,
      "destination",
      destinationField
    );


  const suggestionId =
    mapping.id ??
    mapping.suggestion_id;


  return (
    <>

      <div
        className="drawer-overlay"
        onClick={onClose}
      />


      <aside
        className="mapping-drawer"
        onClick={(event) =>
          event.stopPropagation()
        }
      >

        <div className="drawer-header">

          <div>

            <span className="drawer-eyebrow">
              Mapping Details
            </span>

            <h2>

              {sourceField}

              <span className="drawer-arrow">
                →
              </span>

              {destinationField}

            </h2>

          </div>


          <button
            className="drawer-close"
            onClick={onClose}
          >
            ×
          </button>

        </div>


        <div className="drawer-content">

          <div className="drawer-confidence">

            <div>

              <span>
                Confidence
              </span>

              <strong>
                {confidencePercent}%
              </strong>

            </div>


            <div className="drawer-confidence-bar">

              <div
                style={{
                  width: `${Math.min(
                    confidencePercent,
                    100
                  )}%`,
                }}
              />

            </div>

          </div>


          <DrawerSection
            title="Source"
          >

            <DetailField
              label="Field"
              value={
                sourceField
              }
            />


            <DetailField
              label="Type"
              value={
                sourceColumn?.type ??
                sourceColumn?.data_type ??
                "Not available"
              }
            />


            <DetailField
              label="Nullable"
              value={
                sourceColumn?.nullable ===
                false
                  ? "No"
                  : "Yes"
              }
            />


            <SampleValues
              values={
                sourceSamples
              }
            />

          </DrawerSection>


          <DrawerSection
            title="Destination"
          >

            <DetailField
              label="Field"
              value={
                destinationField
              }
            />


            <DetailField
              label="Type"
              value={
                destinationColumn?.type ??
                destinationColumn?.data_type ??
                "Not available"
              }
            />


            <DetailField
              label="Nullable"
              value={
                destinationColumn?.nullable ===
                false
                  ? "No"
                  : "Yes"
              }
            />


            <SampleValues
              values={
                destinationSamples
              }
            />

          </DrawerSection>


          <DrawerSection
            title="Mapping Evidence"
          >

            <SignalRow
              label="Name similarity"
              value={
                signals.name_similarity
              }
            />


            <SignalRow
              label="Value similarity"
              value={
                signals.value_similarity
              }
            />


            <SignalRow
              label="Type compatibility"
              value={
                signals.type_compatibility
              }
            />


            <SignalRow
              label="Semantic similarity"
              value={
                signals.semantic_similarity
              }
            />


            {mapping.margin !==
              undefined && (

              <SignalRow
                label="Confidence margin"
                value={
                  mapping.margin
                }
              />

            )}

          </DrawerSection>


          <div className="drawer-status">

            <span>
              Status
            </span>


            <span
              className={`match-badge ${
                status ===
                "high_confidence"
                  ? "high"
                  : ""
              }`}
            >
              {status}
            </span>

          </div>

        </div>


        <div className="drawer-footer">

          {approved ? (

            <div className="drawer-approved">

              <CheckCircle2
                size={16}
              />

              Mapping approved

            </div>

          ) : (

            <button
              className="drawer-approve-button"
              disabled={
                approvingId ===
                suggestionId
              }
              onClick={() =>
                onApprove(
                  suggestionId
                )
              }
            >

              {approvingId ===
              suggestionId
                ? "Approving..."
                : "Approve Mapping"}

            </button>

          )}

        </div>

      </aside>

    </>
  );
}


/* =========================================================
   DRAWER SUPPORT COMPONENTS
========================================================= */

function DrawerSection({
  title,
  children,
}) {

  return (

    <section className="drawer-section">

      <h3>
        {title}
      </h3>

      {children}

    </section>

  );
}


function DetailField({
  label,
  value,
}) {

  return (

    <div className="detail-field">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>

  );
}


function SampleValues({
  values,
}) {

  return (

    <div className="sample-values">

      <span className="sample-label">
        Sample values
      </span>


      {values.length === 0 ? (

        <span className="no-samples">
          No sample data available
        </span>

      ) : (

        <div className="sample-list">

          {values
            .slice(0, 5)
            .map(
              (value, index) => (

                <span
                  key={index}
                  className="sample-value"
                >
                  {String(value)}
                </span>

              )
            )}

        </div>

      )}

    </div>

  );
}


function SignalRow({
  label,
  value,
}) {

  if (
    value === undefined ||
    value === null
  ) {

    return null;

  }


  const numericValue =
    Number(value);


  const percentage =
    numericValue <= 1
      ? Math.round(
          numericValue * 100
        )
      : Math.round(
          numericValue
        );


  return (

    <div className="signal-row">

      <span>
        {label}
      </span>


      <div className="signal-value">

        <div className="signal-bar">

          <div
            style={{
              width: `${Math.min(
                percentage,
                100
              )}%`,
            }}
          />

        </div>


        <strong>
          {percentage}%
        </strong>

      </div>

    </div>

  );
}


/* =========================================================
   SCHEMA HELPERS
========================================================= */

function findColumn(
  schema,
  side,
  fieldName
) {

  if (!schema) {
    return null;
  }


  const possibleKeys =
    side === "source"
      ? [
          "source_columns",
          "source_schema",
          "source",
        ]
      : [
          "destination_columns",
          "destination_schema",
          "destination",
        ];


  for (
    const key of possibleKeys
  ) {

    const value =
      schema[key];


    if (
      Array.isArray(value)
    ) {

      const found =
        value.find(
          (column) =>
            column.name ===
              fieldName ||
            column.column_name ===
              fieldName
        );


      if (found) {
        return found;
      }

    }


    if (
      value &&
      typeof value ===
        "object"
    ) {

      for (
        const columns of
        Object.values(value)
      ) {

        if (
          !Array.isArray(
            columns
          )
        ) {
          continue;
        }


        const found =
          columns.find(
            (column) =>
              column.name ===
                fieldName ||
              column.column_name ===
                fieldName
          );


        if (found) {
          return found;
        }

      }

    }

  }


  return null;
}


function getColumnSamples(
  samples,
  side,
  fieldName
) {

  if (!samples) {
    return [];
  }


  const sideSamples =
    side === "source"
      ? samples.source
      : samples.destination;


  if (!sideSamples) {
    return [];
  }


  const values =
    sideSamples[fieldName];


  if (
    !Array.isArray(values)
  ) {
    return [];
  }


  return values;
}


/* =========================================================
   SETTINGS
========================================================= */

function SettingsPage() {

  return (

    <header className="page-header">

      <div>

        <h1>
          Settings
        </h1>

        <p>
          Configure your DataSync environment.
        </p>

      </div>

    </header>

  );
}


function ProtectedRoute({ children }) {
  const token = localStorage.getItem(
    "datasync_token"
  );

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
}


/* =========================================================
   APP LAYOUT
========================================================= */


function AppLayout() {

  return (

    <div className="app-layout">

      <Sidebar />

      <main className="main-content">

        <Routes>

          <Route
            path="/"
            element={
              <Dashboard />
            }
          />


          <Route
            path="/connections"
            element={
              <Connections />
            }
          />

          <Route
            path="/connections/new"
            element={<NewConnection />}
          />

          <Route
            path="/connections/:connectionId"
            element={
              <ConnectionDetails />
            }
          />


          <Route
            path="/settings"
            element={
              <SettingsPage />
            }
          />

        </Routes>

      </main>

    </div>

  );
}


/* =========================================================
   APP
========================================================= */

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/register"
          element={<Register />}
        />

        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}


export default App;