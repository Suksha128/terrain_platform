import re

with open('backend/app/services/terrain_features.py', 'r') as f:
    content = f.read()

# Replace D8 with D-Infinity
old_acc = """    flow_acc_path = str(out / "flow_accumulation.tif")
    if "flow_accumulation" in pre_uploaded:
        paths["flow_accumulation"] = pre_uploaded["flow_accumulation"]
    else:
        wbt.d8_flow_accumulation(
            i=paths["conditioned_dtm"],
            output=flow_acc_path,
            out_type="cells",
            log=False,
            clip=False
        )
        paths["flow_accumulation"] = flow_acc_path"""

new_acc = """    # ADVANCED ACCURACY UPGRADE: Use D-Infinity Flow Accumulation
    # D-Infinity splits flow fractionally across contours for physical accuracy
    flow_acc_path = str(out / "flow_accumulation.tif")
    if "flow_accumulation" in pre_uploaded:
        paths["flow_accumulation"] = pre_uploaded["flow_accumulation"]
    else:
        # First generate D-Inf flow pointer
        d_inf_pntr_path = str(out / "d_inf_pointer.tif")
        wbt.d_inf_pointer(dem=paths["conditioned_dtm"], output=d_inf_pntr_path)
        
        # Calculate D-Inf Specific Catchment Area (SCA)
        wbt.d_inf_flow_accumulation(
            input=d_inf_pntr_path,
            output=flow_acc_path,
            out_type="Specific Catchment Area (SCA)",
            log=False,
            clip=False
        )
        paths["flow_accumulation"] = flow_acc_path"""

content = content.replace(old_acc, new_acc)

with open('backend/app/services/terrain_features.py', 'w') as f:
    f.write(content)
