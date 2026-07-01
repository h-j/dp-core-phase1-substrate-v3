import csv
import json
from pathlib import Path
from jinja2 import Template

class BenchmarkReportRenderer:
    """
    Orchestrates the conversion of aggregated benchmark run metadata into:
    - benchmark_report.json
    - benchmark_report.html (using Jinja2 layout)
    - benchmark_report.csv
    """
    @staticmethod
    def render(benchmark_data: dict, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Save benchmark_report.json
        json_path = output_dir / "benchmark_report.json"
        with open(json_path, "w") as f:
            json.dump(benchmark_data, f, indent=2)
            
        # 2. Render benchmark_report.html
        template_path = Path(__file__).parent / "benchmark_template.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Jinja2 template missing at {template_path}")
            
        with open(template_path, "r") as f:
            template_content = f.read()
            
        template = Template(template_content)
        rendered_html = template.render(**benchmark_data)
        
        html_path = output_dir / "benchmark_report.html"
        with open(html_path, "w") as f:
            f.write(rendered_html)
            
        # 3. Render benchmark_report.csv
        csv_path = output_dir / "benchmark_report.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Asset", "Category", "Prediction Accuracy", "Calibration Error", 
                "Knowledge Debt", "Memory Reuse", "Contradiction Pressure", "Principles Count"
            ])
            for asset in benchmark_data.get("assets_summary", []):
                writer.writerow([
                    asset.get("symbol"),
                    asset.get("category"),
                    f"{asset.get('accuracy'):.2f}%",
                    f"{asset.get('calibration_error') * 100.0:.2f}%",
                    asset.get("knowledge_debt"),
                    f"{asset.get('memory_reuse') * 100.0:.2f}%",
                    f"{asset.get('contradiction_pressure'):.4f}",
                    asset.get("principles_count")
                ])
                
        print(f"✓ Successfully rendered Multi-Asset Benchmark files to: {output_dir}")
