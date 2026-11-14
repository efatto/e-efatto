-- connector_whs exchanges stock lists with the customer's MSSQL WMS.  A
-- neutralized database is meant to be copied around, so it must not be able to
-- reach only the production WMS: wipe the connection string but do not archive
-- the data sources, nor wipe the password, used to connect the test source.
-- ``conn_string`` embeds the WMS user, host and database, ``password`` is
-- stored in clear and is used from both the production and the test
-- connection, so preserve it.
UPDATE base_external_dbsource
   SET conn_string = NULL,
       client_cert = NULL,
       client_key = NULL
 WHERE connector = 'mssql';

-- ``base`` already disables every cron when neutralizing; switch the connector
-- jobs off explicitly too, so that re-enabling a job on the copy cannot start a
-- synchronization (the credentials above are gone anyway).
UPDATE ir_cron
   SET active = false
 WHERE id IN (
       SELECT res_id
         FROM ir_model_data
        WHERE module = 'connector_whs'
          AND model = 'ir.cron'
);
