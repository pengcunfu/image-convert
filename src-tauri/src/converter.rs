use anyhow::{Context, Result};
use image::{DynamicImage, ImageEncoder, ImageFormat};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Serialize, Deserialize)]
pub struct ConvertRequest {
    pub input_paths: Vec<String>,
    pub output_dir: String,
    pub output_format: String,
    pub quality: u8,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ConvertResult {
    pub success: bool,
    pub total: usize,
    pub converted: usize,
    pub failed: usize,
    pub errors: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FileConversionResult {
    pub file_name: String,
    pub success: bool,
    pub error: Option<String>,
}

/// Parse format string to ImageFormat
fn parse_format(format_str: &str) -> Result<ImageFormat> {
    match format_str.to_lowercase().as_str() {
        "jpg" | "jpeg" => Ok(ImageFormat::Jpeg),
        "png" => Ok(ImageFormat::Png),
        "gif" => Ok(ImageFormat::Gif),
        "bmp" => Ok(ImageFormat::Bmp),
        "ico" => Ok(ImageFormat::Ico),
        "tiff" | "tif" => Ok(ImageFormat::Tiff),
        "webp" => Ok(ImageFormat::WebP),
        _ => Err(anyhow::anyhow!("Unsupported format: {}", format_str)),
    }
}

/// Get file extension for format
fn get_extension(format: &ImageFormat) -> &str {
    match format {
        ImageFormat::Jpeg => "jpg",
        ImageFormat::Png => "png",
        ImageFormat::Gif => "gif",
        ImageFormat::Bmp => "bmp",
        ImageFormat::Ico => "ico",
        ImageFormat::Tiff => "tiff",
        ImageFormat::WebP => "webp",
        _ => "jpg",
    }
}

/// Convert a single image file
fn convert_single_image(
    input_path: &Path,
    output_dir: &Path,
    output_format: ImageFormat,
    quality: u8,
) -> Result<()> {
    // Load the image
    let img = image::open(input_path).context(format!("Failed to open image: {:?}", input_path))?;

    // Handle transparency for formats that don't support it
    let img = if matches!(output_format, ImageFormat::Jpeg | ImageFormat::Bmp) {
        // Convert RGBA to RGB with white background
        if img.color().has_alpha() {
            DynamicImage::ImageRgb8(img.to_rgb8())
        } else {
            img
        }
    } else {
        img
    };

    // Create output filename
    let file_stem = input_path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("output");
    let extension = get_extension(&output_format);
    let output_path = output_dir.join(format!("{}.{}", file_stem, extension));

    // Save the image
    match output_format {
        ImageFormat::Jpeg => {
            let mut encoder = image::codecs::jpeg::JpegEncoder::new_with_quality(
                fs::File::create(&output_path)?,
                quality,
            );
            encoder.encode_image(&img)?;
        }
        ImageFormat::Png => {
            let encoder = image::codecs::png::PngEncoder::new_with_quality(
                fs::File::create(&output_path)?,
                image::codecs::png::CompressionType::Best,
                image::codecs::png::FilterType::Adaptive,
            );
            encoder.write_image(img.as_bytes(), img.width(), img.height(), img.color())?;
        }
        _ => {
            img.save_with_format(&output_path, output_format)?;
        }
    }

    Ok(())
}

/// Main conversion function exposed to Tauri
#[tauri::command]
pub fn convert_images(request: ConvertRequest) -> ConvertResult {
    // Validate output directory
    let output_dir = PathBuf::from(&request.output_dir);
    if let Err(e) = fs::create_dir_all(&output_dir) {
        return ConvertResult {
            success: false,
            total: 0,
            converted: 0,
            failed: 0,
            errors: vec![format!("Failed to create output directory: {}", e)],
        };
    }

    // Parse output format
    let output_format = match parse_format(&request.output_format) {
        Ok(fmt) => fmt,
        Err(e) => {
            return ConvertResult {
                success: false,
                total: 0,
                converted: 0,
                failed: 0,
                errors: vec![format!("Invalid output format: {}", e)],
            };
        }
    };

    // Clamp quality to valid range
    let quality = request.quality.clamp(1, 100);

    // Process all files in parallel
    let results: Vec<FileConversionResult> = request
        .input_paths
        .par_iter()
        .map(|path_str| {
            let input_path = PathBuf::from(path_str);
            let file_name = input_path
                .file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("unknown")
                .to_string();

            match convert_single_image(&input_path, &output_dir, output_format, quality) {
                Ok(_) => FileConversionResult {
                    file_name,
                    success: true,
                    error: None,
                },
                Err(e) => FileConversionResult {
                    file_name,
                    success: false,
                    error: Some(e.to_string()),
                },
            }
        })
        .collect();

    // Aggregate results
    let total = results.len();
    let converted = results.iter().filter(|r| r.success).count();
    let failed = total - converted;
    let errors: Vec<String> = results
        .iter()
        .filter_map(|r| {
            r.error
                .as_ref()
                .map(|err| format!("{}: {}", r.file_name, err))
        })
        .collect();

    ConvertResult {
        success: failed == 0,
        total,
        converted,
        failed,
        errors,
    }
}
