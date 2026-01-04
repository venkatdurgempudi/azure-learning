-- Sample DDL: create mock tables in local SQL Server for Registrations dashboard

CREATE DATABASE mock_his;
GO
USE mock_his;
GO

-- Master tables
CREATE TABLE gender_master (
  gender_id INT PRIMARY KEY,
  gender_desc VARCHAR(50)
);

CREATE TABLE unit_master (
  unit_id INT PRIMARY KEY,
  unit_name VARCHAR(100),
  facility_id INT
);

-- Transaction table: patient_registrations
CREATE TABLE patient_registrations (
  registration_id INT PRIMARY KEY,
  patient_id INT,
  reg_dt DATETIME2,
  unit_id INT,
  gender_id INT,
  source VARCHAR(50),
  created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
  modified_at DATETIME2 DEFAULT SYSUTCDATETIME()
);

-- Control table for runs (if you use Azure SQL for metadata)
CREATE TABLE pipeline_runs (
  run_id VARCHAR(100) PRIMARY KEY,
  pipeline_name VARCHAR(100),
  start_ts DATETIME2,
  end_ts DATETIME2,
  window_start DATE,
  window_end DATE,
  rows_extracted INT,
  rows_merged INT,
  status VARCHAR(20),
  error_message NVARCHAR(MAX)
);
GO
