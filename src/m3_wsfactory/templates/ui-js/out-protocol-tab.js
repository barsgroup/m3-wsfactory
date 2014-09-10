/**
 * Created by tim on 10.09.14.
 */
var outProtocolGrid = Ext.getCmp("{{ component.OutProtocol_param_grid.client_id }}");
setGridCellEditor(outProtocolGrid, "valueEditor");
submitGridStore(win, outProtocolGrid, "OutProtocol");

var outProtocolField = Ext.getCmp("{{ component.OutProtocol_field.client_id }}");
outProtocolField.on("change", function (cmp, value) {
  var currentValue = this.getStore().baseParams["protocol_code"];
  if (currentValue !== value) {
    this.getStore().setBaseParam("protocol_code", value);
    this.getStore().reload();
  }
}, outProtocolGrid);