import pytest
import os
from pathlib import Path
from tools.registry import write_to_md, write_to_pdf, create_1d_plot, read_text, list_directory, calculator

def test_write_to_md(tmp_path):
    res = write_to_md("test_report.md", "Test Title", "## Section 1\nThis is a test report content.")
    assert "saved successfully" in res.lower()
    
    output_path = Path("output/test_report.md")
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Test Title" in content
    assert "Section 1" in content

def test_write_to_pdf():
    res = write_to_pdf("test_pdf.pdf", "PDF Test Title", "## Section 1\nPDF content body text.")
    assert "pdf saved successfully" in res.lower()
    assert Path("output/test_pdf.pdf").exists()

def test_create_1d_plot_formula():
    res = create_1d_plot("sin(x)", "X Axis", "Y Axis", "Sin Plot Test")
    assert "plot created successfully" in res.lower()
    assert Path("output/Sin_Plot_Test.png").exists()

def test_read_text(tmp_path):
    file_p = tmp_path / "sample.txt"
    file_p.write_text("Hello ORC Test", encoding="utf-8")
    
    res = read_text(str(file_p))
    assert "Hello ORC Test" in res

def test_list_directory(tmp_path):
    (tmp_path / "sub_file.txt").write_text("dummy", encoding="utf-8")
    res = list_directory(str(tmp_path))
    assert "sub_file.txt" in res

def test_calculator_native():
    assert calculator("100 / 4") == "25.0"
    assert calculator("sin(0)") == "0.0"
