import requests
import csv
import os

# Output folder
output_dir = r"C:\Users\marti\Desktop\create_dataset_utils\allen_svg_coronal"
os.makedirs(output_dir, exist_ok=True)

# Step 1: Get list of AtlasImage IDs with Structure boundaries (GraphicGroupLabel.id=28)
csv_url = ("http://api.brain-map.org/api/v2/data/query.csv?"
           "criteria=model::AtlasImage,"
           "rma::criteria,atlas_data_set(atlases[id$eq1]),"
           "graphic_objects(graphic_group_label[id$eq28]),"
           "rma::options[tabular$eq'sub_images.id'][order$eq'sub_images.id']"
           "&num_rows=all&start_row=0")

print("Downloading list of SectionImage IDs...")
response = requests.get(csv_url)
response.raise_for_status()

# Parse CSV to get SectionImage IDs
lines = response.text.splitlines()
reader = csv.DictReader(lines)
section_ids = [row['id'] for row in reader]

print(f"Found {len(section_ids)} SectionImages with structure boundaries.")

# Step 2: Download SVG for each SectionImage
for sec_id in section_ids:
    svg_url = f"http://api.brain-map.org/api/v2/svg_download/{sec_id}?groups=28"
    out_file = os.path.join(output_dir, f"{sec_id}.svg")
    
    try:
        r = requests.get(svg_url)
        r.raise_for_status()
        with open(out_file, 'wb') as f:
            f.write(r.content)
        print(f"Downloaded SectionImage {sec_id} -> {out_file}")
    except Exception as e:
        print(f"Failed to download SectionImage {sec_id}: {e}")

print("All downloads finished.")
