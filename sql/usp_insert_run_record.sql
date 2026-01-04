-- Optional Stored Procedure in Azure SQL to write pipeline run metadata
CREATE PROCEDURE usp_InsertRunRecord
    @run_id VARCHAR(100),
    @pipeline_name VARCHAR(100),
    @start_ts DATETIME2 = NULL,
    @end_ts DATETIME2 = NULL,
    @window_start DATE = NULL,
    @window_end DATE = NULL,
    @rows_extracted INT = NULL,
    @rows_merged INT = NULL,
    @status VARCHAR(20) = 'Running',
    @error_message NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM pipeline_runs WHERE run_id = @run_id)
    BEGIN
        UPDATE pipeline_runs
        SET pipeline_name=@pipeline_name, start_ts=@start_ts, end_ts=@end_ts,
            window_start=@window_start, window_end=@window_end,
            rows_extracted=@rows_extracted, rows_merged=@rows_merged,
            status=@status, error_message=@error_message
        WHERE run_id=@run_id;
    END
    ELSE
    BEGIN
        INSERT INTO pipeline_runs (run_id, pipeline_name, start_ts, end_ts, window_start, window_end, rows_extracted, rows_merged, status, error_message)
        VALUES (@run_id, @pipeline_name, @start_ts, @end_ts, @window_start, @window_end, @rows_extracted, @rows_merged, @status, @error_message);
    END
END
