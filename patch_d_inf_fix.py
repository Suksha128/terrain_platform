import re

with open('backend/app/services/terrain_features.py', 'r') as f:
    content = f.read()

# Replace the D-Inf block to output both D8 and D-Inf
new_acc = """    # Calculate D8 for Stream Extraction & Basins (requires cell counts)
    flow_acc_path = str(out / "flow_accumulation.tif")
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
        paths["flow_accumulation"] = flow_acc_path

    # ADVANCED ACCURACY: Calculate D-Infinity SCA exclusively for highly accurate TWI
    d_inf_sca_path = str(out / "d_inf_sca.tif")
    d_inf_pntr_path = str(out / "d_inf_pointer.tif")
    wbt.d_inf_pointer(dem=paths["conditioned_dtm"], output=d_inf_pntr_path)
    wbt.d_inf_flow_accumulation(
        input=d_inf_pntr_path,
        output=d_inf_sca_path,
        out_type="Specific Catchment Area (SCA)",
        log=False,
        clip=False
    )
    paths["d_inf_sca"] = d_inf_sca_path"""

# Need to find the exact block we just patched and replace it
# Or just replace the whole flow_accumulation generation
content = re.sub(r'    # ADVANCED ACCURACY UPGRADE:.*?paths\["flow_accumulation"\] = flow_acc_path', new_acc, content, flags=re.DOTALL)

# And update the TWI call to use d_inf_sca
twi_old = """    twi_path = str(out / "twi.tif")
    if "twi" in pre_uploaded:
        paths["twi"] = pre_uploaded["twi"]
    else:
        wbt.wetness_index(
            sca=paths["flow_accumulation"],
            slope=paths["slope"],
            output=twi_path,
        )
        paths["twi"] = twi_path"""

twi_new = """    twi_path = str(out / "twi.tif")
    if "twi" in pre_uploaded:
        paths["twi"] = pre_uploaded["twi"]
    else:
        wbt.wetness_index(
            sca=paths["d_inf_sca"],
            slope=paths["slope"],
            output=twi_path,
        )
        paths["twi"] = twi_path"""

content = content.replace(twi_old, twi_new)

with open('backend/app/services/terrain_features.py', 'w') as f:
    f.write(content)
