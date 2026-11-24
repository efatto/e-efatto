# n.b. test_connector_wms_whs runs only on local with a dedicated VM with
# "--test-tags=test_wms"; test_hyddemo_whs_packing does not need the MSSQL server
from . import test_connector_wms_whs
from . import test_hyddemo_whs_packing
