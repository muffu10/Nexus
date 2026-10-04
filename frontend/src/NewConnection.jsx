import { useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  Plus,
} from "lucide-react";
import {
  useNavigate,
} from "react-router-dom";

import api from "./api/client";


function NewConnection() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [destinationUrl, setDestinationUrl] =
    useState("");

  const [sourceTables, setSourceTables] =
    useState([]);

  const [destinationTables, setDestinationTables] =
    useState([]);

  const [sourceTable, setSourceTable] =
    useState("");

  const [destinationTable, setDestinationTable] =
    useState("");

  const [connected, setConnected] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [creating, setCreating] =
    useState(false);

  const [error, setError] =
    useState("");


  async function handleTestConnection() {
    setError("");
    setConnected(false);

    if (!sourceUrl.trim()) {
      setError(
        "Please enter the source PostgreSQL URL."
      );
      return;
    }

    if (!destinationUrl.trim()) {
      setError(
        "Please enter the destination PostgreSQL URL."
      );
      return;
    }

    setLoading(true);

    try {
      const response = await api.post(
        "/connections/test",
        {
          source_type: "postgresql",
          source_url: sourceUrl,
          destination_type: "postgresql",
          destination_url: destinationUrl,
        }
      );

      const data = response.data;

      setSourceTables(
        data.source_tables || []
      );

      setDestinationTables(
        data.destination_tables || []
      );

      setSourceTable("");
      setDestinationTable("");

      setConnected(true);

    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Could not connect to the databases."
      );

    } finally {
      setLoading(false);
    }
  }


  async function handleCreateConnection() {
    setError("");

    if (!name.trim()) {
      setError(
        "Please enter a connection name."
      );
      return;
    }

    if (!sourceTable) {
      setError(
        "Please select a source table."
      );
      return;
    }

    if (!destinationTable) {
      setError(
        "Please select a destination table."
      );
      return;
    }

    setCreating(true);

    try {
      const response = await api.post(
        "/connections",
        {
          name,
          source_type: "postgresql",
          source_url: sourceUrl,
          destination_type: "postgresql",
          destination_url: destinationUrl,
          source_table: sourceTable,
          destination_table: destinationTable,
        }
      );

      navigate(
        `/connections/${response.data.id}`
      );

    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Could not create the connection."
      );

    } finally {
      setCreating(false);
    }
  }


  return (
    <div>

      {/* =================================================
          PAGE HEADER
      ================================================= */}

      <header className="page-header">

        <div>
          <h1>New Connection</h1>

          <p>
            Connect two PostgreSQL databases
            and choose the tables to synchronize.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={() =>
            navigate("/connections")
          }
        >
          <ArrowLeft size={16} />
          Back
        </button>

      </header>


      {/* =================================================
          ERROR
      ================================================= */}

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}


      {/* =================================================
          CONNECTION DETAILS
      ================================================= */}

      <section className="content-card">

        <div className="card-header new-connection-header">

          <div>
            <h2>
              Connection Details
            </h2>

            <p>
              Enter the database connection
              URLs.
            </p>
          </div>

        </div>


        <div
          style={{
            display: "grid",
            gap: "20px",
            maxWidth: "760px",
            paddingTop: "20px",
          }}
        >

          {/* CONNECTION NAME */}

          <div className="connection-form-field">

            <label htmlFor="connection-name">
              Connection Name
            </label>

            <input
              id="connection-name"
              type="text"
              autoComplete="off"
              value={name}
              onChange={(e) =>
                setName(e.target.value)
              }
              placeholder="e.g. Production → Analytics"
            />

          </div>


          {/* SOURCE URL */}

          <div className="connection-form-field">

            <label htmlFor="source-url">
              Source PostgreSQL URL
            </label>

            <input
              id="source-url"
              type="password"
              autoComplete="new-password"
              value={sourceUrl}
              onChange={(e) =>
                setSourceUrl(e.target.value)
              }
              placeholder="postgresql://username:password@host:5432/database"
            />

          </div>


          {/* DESTINATION URL */}

          <div className="connection-form-field">

            <label htmlFor="destination-url">
              Destination PostgreSQL URL
            </label>

            <input
              id="destination-url"
              type="password"
              autoComplete="new-password"
              value={destinationUrl}
              onChange={(e) =>
                setDestinationUrl(
                  e.target.value
                )
              }
              placeholder="postgresql://username:password@host:5432/database"
            />

          </div>


          {/* TEST CONNECTION */}

          <button
            className="primary-button"
            onClick={handleTestConnection}
            disabled={
              loading ||
              !sourceUrl ||
              !destinationUrl
            }
          >

            {loading ? (
              "Connecting..."
            ) : (
              <>
                <Plus size={16} />
                Test & Connect
              </>
            )}

          </button>

        </div>

      </section>


      {/* =================================================
          TABLE SELECTION
      ================================================= */}

      {connected && (

        <section
          className="content-card"
          style={{
            marginTop: "20px",
          }}
        >

          <div className="card-header">

            <div>

              <h2
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <CheckCircle2
                  size={18}
                />

                Databases Connected
              </h2>

              <p>
                Select the tables you want
                DataSync to synchronize.
              </p>

            </div>

          </div>


          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "1fr 1fr",
              gap: "24px",
            }}
          >

            {/* SOURCE TABLE */}

            <div className="connection-form-field">

              <label htmlFor="source-table">
                Source Table
              </label>

              <select
                id="source-table"
                value={sourceTable}
                onChange={(e) =>
                  setSourceTable(
                    e.target.value
                  )
                }
              >

                <option value="">
                  Select source table
                </option>

                {sourceTables.map(
                  (table) => (
                    <option
                      key={table}
                      value={table}
                    >
                      {table}
                    </option>
                  )
                )}

              </select>

            </div>


            {/* DESTINATION TABLE */}

            <div className="connection-form-field">

              <label htmlFor="destination-table">
                Destination Table
              </label>

              <select
                id="destination-table"
                value={destinationTable}
                onChange={(e) =>
                  setDestinationTable(
                    e.target.value
                  )
                }
              >

                <option value="">
                  Select destination table
                </option>

                {destinationTables.map(
                  (table) => (
                    <option
                      key={table}
                      value={table}
                    >
                      {table}
                    </option>
                  )
                )}

              </select>

            </div>

          </div>


          {/* CREATE CONNECTION */}

          <div
            style={{
              marginTop: "24px",
            }}
          >

            <button
              className="primary-button"
              onClick={
                handleCreateConnection
              }
              disabled={
                creating ||
                !sourceTable ||
                !destinationTable
              }
            >

              {creating
                ? "Creating..."
                : "Create Connection"}

            </button>

          </div>

        </section>

      )}

    </div>
  );
}


export default NewConnection;