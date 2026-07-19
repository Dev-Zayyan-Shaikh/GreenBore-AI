import os

# Define the seed documents with rich technical content
SEED_DOCUMENTS = {
    "groundwater_resistivity_guide.txt": """Title: Petrophysical Resistivity Guide for Groundwater Exploration
Author: GreenBore AI Research Group
Category: Resistivity & Hydrogeology
Status: Synthetic reference document

Overview:
Electrical resistivity is one of the most critical sensor measurements used to identify water-bearing formations. Since water is a good conductor when it contains dissolved solids, water-bearing zones exhibit significantly lower electrical resistivity compared to tight, dry rock matrices.

Interpretation Rules:
1. Very Low Resistivity (< 50 Ohm-m): Often indicates clay-rich formations or saline groundwater. Clay holds water but has low permeability, making it a poor aquifer target.
2. Moderate Resistivity (50 - 250 Ohm-m): The primary target zone for fresh-water aquifers, particularly in sandstone, gravel, or fractured limestone.
3. High Resistivity (> 500 Ohm-m): Typically indicates dense, non-porous rock types like massive granite, basalt, or tight limestone with little to no groundwater presence, unless heavily fractured.

Correlation with Porosity:
Resistivity must always be analyzed alongside porosity. A formation with high porosity and low-to-moderate resistivity is a classic indicator of a productive aquifer. If porosity is low but resistivity is high, the rock is tight and dry.
""",

    "porosity_permeability_aquifers.txt": """Title: Porosity and Permeability Characteristics of Groundwater Aquifers
Author: Geological Survey of GreenBore
Category: Porosity & Aquifers
Status: Synthetic reference document

Overview:
Porosity and permeability determine the capacity of a geological formation to store and transmit groundwater. 
- Porosity is the percentage of void space in a rock or soil.
- Permeability is the measure of the ease with which a fluid can flow through the formation's interconnected pore spaces.

Aquifer Materials and Porosity Ranges:
1. Sandstone: Exhibits moderate to high porosity (10% to 30%) and high permeability. Excellent aquifer material because the pore spaces are well-connected.
2. Limestone: Can have low primary porosity, but secondary porosity (fractures, dissolution channels, caves) can range from 5% to 20%, resulting in extremely high localized permeability.
3. Clay and Shale: Possess very high porosity (up to 50%) but extremely low permeability due to tiny, isolated pore spaces. They act as aquitards (confining layers) that block water flow.
4. Granite and Igneous Rocks: Have negligible primary porosity (< 1%) and permeability. They only yield water if they contain active fracture systems.

Key Indicators:
- A high porosity_resistivity_ratio is a strong signature of highly porous, saturated zones.
- Well-sorted sand deposits yield the highest permeability and are the easiest to develop for high-yield wells.
""",

    "fracture_zones_groundwater.txt": """Title: Characterization of Fracture Zones in Hard Rock Groundwater Aquifers
Author: Dr. Marcus Vance, Hydrogeologist
Category: Fracture Systems
Status: Synthetic reference document

Overview:
In hard rock terrains (such as granites, gneisses, and dense limestones), groundwater is stored and transmitted almost exclusively through fractures, joints, and fault zones. These are known as fractured rock aquifers.

Identifying Fracture Zones in Borehole Logs:
1. Resistivity Drops: Sharp, localized decreases in resistivity measurements within otherwise high-resistivity rock indicate water-filled fractures.
2. Gamma-Ray Spikes: Sometimes clay or mineral deposits fill fractures, leading to higher gamma-ray readings. However, clean, water-filled fractures will not show gamma spikes.
3. Sonic Travel Time Increases: Fractures cause acoustic waves to slow down. A localized increase in sonic travel time (slowing of wave propagation) indicates mechanical fractures or high-porosity intervals.
4. Density Decreases: Bulk density drops significantly in fractured zones compared to competent, massive rock.

Drilling Implications:
Drilling should be targeted to intersect major sub-vertical fracture networks. If a borehole is drilled entirely in massive, unfractured granite, it will remain dry regardless of the depth.
""",

    "well_drilling_casing_standards.txt": """Title: Standard Operating Procedures for Water Well Casing and Design
Author: GreenBore Well Drilling Engineering Team
Category: Well Design & Casing
Status: Synthetic reference document

Overview:
Proper well design is crucial to prevent borehole collapse, seal off contaminated shallow aquifers, and maximize freshwater yields. The key components of well design are casing selection, screen placement, and gravel packing.

Well Casing Selection Guidelines:
1. Solid Steel Casing: Used in unconsolidated materials (clay, sand, gravel) to keep the hole open. In hard, stable rock (like massive granite or dense limestone), casing is often not required for the entire depth, and an open-hole design is used.
2. PVC Casing: Suitable for shallow, low-corrosive wells. Steel is preferred for deep wells (> 100 meters) due to structural load.
3. Grouting: The annular space between the casing and the borehole wall must be filled with cement grout down to at least 15 meters to prevent surface run-off contamination.

Well Screen and Slot Design:
- Well screens must be placed precisely adjacent to the identified water-bearing zone (aquifer).
- Placing screens adjacent to clay or shale layers will lead to muddy water, well siltation, and low yields.
- Slot size must match the grain size of the aquifer material. For sandstone, a screen slot size of 0.5 mm to 1.0 mm is standard, accompanied by a clean gravel pack.
""",

    "rock_types_aquifer_behavior.txt": """Title: Rock Type Classification and Hydrogeological Behavior
Author: Earth Science Research Institute
Category: Rock Classification
Status: Synthetic reference document

Overview:
Different rock types exhibit distinct physical properties that directly govern their water-bearing potential.

Classification System:
1. Sandstone (Rock Code 1): Sedimentary rock composed of sand grains. Typically has high porosity and high permeability. Highly favorable for water wells.
2. Limestone (Rock Code 2): Carbonate sedimentary rock. Can be dense and tight, but frequently hosts secondary water-bearing networks via fractures and karst dissolution. Highly variable but potentially excellent yields.
3. Claystone / Shale (Rock Code 0 or 3): Fine-grained sedimentary rocks. High clay content. Act as confining layers (aquitards) that seal aquifers. Do not drill screens in these zones.
4. Granite / Igneous (Rock Code 4): Crystalline rock. Water presence is strictly dependent on fractures. Massive granite is completely dry and serves as a natural barrier.

Summary Matrix:
- Sandstone: High porosity, high permeability, low resistivity (when saturated).
- Limestone: Low-to-moderate porosity, high fracture permeability, variable resistivity.
- Claystone: High porosity, very low permeability, very low resistivity (due to clay minerals, not water yield).
- Granite: Low porosity, low permeability, high resistivity (except in water-bearing fracture zones).
""",

    "sensor_anomaly_troubleshooting.txt": """Title: Troubleshooting Guide: Borehole Log Sensor Anomalies and Noise
Author: GreenBore Sensor Calibration Lab
Category: Instrumentation & QA
Status: Synthetic reference document

Overview:
Borehole logging instruments operate in harsh, high-pressure, and fluid-filled environments. Understanding and correcting sensor anomalies is critical to avoid false predictions of water presence.

Common Sensor Anomalies:
1. Resistivity Washout: If the borehole diameter expands significantly (washout), the resistivity sensor measures the drilling mud instead of the formation, resulting in an artificially low resistivity reading (often close to 1-10 Ohm-m). Cross-reference with density logs; washouts also cause erratic density drops.
2. Clay-Induced Low Resistivity: Clay minerals conduct electricity, causing low resistivity. This can be mistaken for water. To differentiate, check the Gamma-Ray log. High Gamma-Ray readings (> 100 API) indicate clay/shale, while low Gamma-Ray (< 50 API) combined with low resistivity indicates a true freshwater sand aquifer.
3. Cycle Skipping in Sonic Logs: Occurs when the sonic transmitter signal is attenuated by fractures or gas, causing the receiver to miss the first wave arrival. This results in sudden, abnormally high spikes in sonic travel time.
4. Sensor Noise Calibration: Raw logs should be smoothed using a 5-point moving average (MA5) to eliminate Gaussian electronic noise without distorting formation boundaries.
"""
}


def seed_knowledge_base():
    # Define destination path
    dest_dir = "datasets/geological_knowledge"
    os.makedirs(dest_dir, exist_ok=True)
    
    print(f"Creating synthetic geological knowledge base in: {dest_dir}")
    
    for filename, content in SEED_DOCUMENTS.items():
        filepath = os.path.join(dest_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f" - Created {filename} ({len(content)} bytes)")
        
    print("Knowledge base seeding complete.")


if __name__ == "__main__":
    seed_knowledge_base()
