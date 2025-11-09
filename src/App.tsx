import { useState } from "react";
import { open } from "@tauri-apps/api/dialog";
import { invoke } from "@tauri-apps/api/tauri";
import {
  Button,
  Card,
  Select,
  Slider,
  Space,
  Typography,
  message,
  Statistic,
  Row,
  Col,
  Checkbox,
  Alert,
  Divider,
  List,
} from "antd";
import {
  FolderOpenOutlined,
  FileImageOutlined,
  SyncOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SettingOutlined,
  PictureOutlined,
} from "@ant-design/icons";
import type { CheckboxChangeEvent } from "antd/es/checkbox";

const { Title, Text } = Typography;

interface ConvertResult {
  success: boolean;
  total: number;
  converted: number;
  failed: number;
  errors: string[];
}

const SUPPORTED_FORMATS = [
  { value: "jpg", label: "JPEG (.jpg)" },
  { value: "png", label: "PNG (.png)" },
  { value: "gif", label: "GIF (.gif)" },
  { value: "bmp", label: "BMP (.bmp)" },
  { value: "webp", label: "WebP (.webp)" },
  { value: "tiff", label: "TIFF (.tiff)" },
  { value: "ico", label: "ICO (.ico)" },
];

function App() {
  const [inputFiles, setInputFiles] = useState<string[]>([]);
  const [outputDir, setOutputDir] = useState<string>("");
  const [outputFormat, setOutputFormat] = useState<string>("jpg");
  const [quality, setQuality] = useState<number>(100);
  const [isConverting, setIsConverting] = useState<boolean>(false);
  const [result, setResult] = useState<ConvertResult | null>(null);
  const [useSourceDir, setUseSourceDir] = useState<boolean>(false);

  const handleSelectFiles = async () => {
    try {
      const selected = await open({
        multiple: true,
        filters: [
          {
            name: "Images",
            extensions: ["jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "tif", "ico"],
          },
        ],
      });

      if (selected && Array.isArray(selected)) {
        setInputFiles(selected);
        setResult(null);
        message.success(`已选择 ${selected.length} 个文件`);
      }
    } catch (error) {
      console.error("Error selecting files:", error);
      message.error("选择文件失败");
    }
  };

  const handleSelectOutputDir = async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
      });

      if (selected && typeof selected === "string") {
        setOutputDir(selected);
        message.success("已选择输出目录");
      }
    } catch (error) {
      console.error("Error selecting directory:", error);
      message.error("选择目录失败");
    }
  };

  const handleConvert = async () => {
    if (inputFiles.length === 0) {
      message.warning("请先选择要转换的图片文件");
      return;
    }

    if (!useSourceDir && !outputDir) {
      message.warning("请选择输出目录或勾选'使用源文件目录'");
      return;
    }

    setIsConverting(true);
    setResult(null);

    try {
      // 如果使用源目录，则为每个文件使用其所在目录
      let finalOutputDir = outputDir;
      if (useSourceDir && inputFiles.length > 0) {
        // 获取第一个文件的目录作为输出目录
        const firstFilePath = inputFiles[0];
        const lastSlash = Math.max(
          firstFilePath.lastIndexOf("/"),
          firstFilePath.lastIndexOf("\\")
        );
        if (lastSlash !== -1) {
          finalOutputDir = firstFilePath.substring(0, lastSlash);
        }
      }

      const convertResult: ConvertResult = await invoke("convert_images", {
        request: {
          input_paths: inputFiles,
          output_dir: finalOutputDir,
          output_format: outputFormat,
          quality: quality,
        },
      });

      setResult(convertResult);
      if (convertResult.success) {
        message.success("转换完成！");
      } else {
        message.error("转换过程中出现错误");
      }
    } catch (error) {
      console.error("Conversion error:", error);
      message.error("转换失败: " + String(error));
      setResult({
        success: false,
        total: inputFiles.length,
        converted: 0,
        failed: inputFiles.length,
        errors: [String(error)],
      });
    } finally {
      setIsConverting(false);
    }
  };

  const handleReset = () => {
    setInputFiles([]);
    setOutputDir("");
    setResult(null);
    setUseSourceDir(false);
    message.info("已重置所有设置");
  };

  const onUseSourceDirChange = (e: CheckboxChangeEvent) => {
    setUseSourceDir(e.target.checked);
    if (e.target.checked) {
      setOutputDir("");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f0f2f5", padding: "16px" }}>
      <div style={{ maxWidth: 1000, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <Space direction="vertical" size={4}>
            <PictureOutlined style={{ fontSize: 36, color: "#1890ff" }} />
            <Title level={2} style={{ margin: 0, marginBottom: 4 }}>图片格式转换器</Title>
            <Text type="secondary" style={{ fontSize: 14 }}>
              支持批量转换、多种格式互转，基于 Rust + Tauri 构建
            </Text>
          </Space>
        </div>

        {/* Main Content */}
        <Card bodyStyle={{ padding: "20px" }}>
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            {/* File Selection */}
            <div>
              <Space style={{ marginBottom: 8 }}>
                <FileImageOutlined style={{ fontSize: 16, color: "#1890ff" }} />
                <Text strong>选择图片文件</Text>
              </Space>
              <Button
                type="primary"
                icon={<FolderOpenOutlined />}
                onClick={handleSelectFiles}
                block
              >
                {inputFiles.length > 0
                  ? `已选择 ${inputFiles.length} 个文件`
                  : "点击选择图片文件"}
              </Button>
              {inputFiles.length > 0 && (
                <Card
                  size="small"
                  bodyStyle={{ padding: "8px 12px" }}
                  style={{ marginTop: 8, maxHeight: 150, overflow: "auto" }}
                >
                  <List
                    size="small"
                    split={false}
                    dataSource={inputFiles}
                    renderItem={(file) => (
                      <List.Item style={{ padding: "4px 0", border: "none" }}>
                        <Text ellipsis title={file} style={{ fontSize: 13 }}>
                          {file.split(/[\\\/]/).pop()}
                        </Text>
                      </List.Item>
                    )}
                  />
                </Card>
              )}
            </div>

            {/* Output Directory */}
            <div>
              <Space style={{ marginBottom: 8 }}>
                <FolderOpenOutlined style={{ fontSize: 16, color: "#1890ff" }} />
                <Text strong>输出目录</Text>
              </Space>
              
              <Checkbox
                checked={useSourceDir}
                onChange={onUseSourceDirChange}
                style={{ marginBottom: 8 }}
              >
                使用源文件所在目录
              </Checkbox>

              <Button
                icon={<FolderOpenOutlined />}
                onClick={handleSelectOutputDir}
                disabled={useSourceDir}
                block
              >
                {useSourceDir 
                  ? "已选择使用源文件目录" 
                  : (outputDir || "点击选择输出目录")}
              </Button>
              {outputDir && !useSourceDir && (
                <Text type="secondary" style={{ marginTop: 6, display: "block", fontSize: 12 }} ellipsis>
                  {outputDir}
                </Text>
              )}
            </div>

            <Divider style={{ margin: "16px 0" }} />

            {/* Settings */}
            <div>
              <Space style={{ marginBottom: 8 }}>
                <SettingOutlined style={{ fontSize: 16, color: "#1890ff" }} />
                <Text strong>转换设置</Text>
              </Space>
              <Row gutter={16}>
                {/* Format Selection */}
                <Col xs={24} sm={12}>
                  <div style={{ marginBottom: 4 }}>
                    <Text>输出格式</Text>
                  </div>
                  <Select
                    value={outputFormat}
                    onChange={setOutputFormat}
                    style={{ width: "100%" }}
                    options={SUPPORTED_FORMATS}
                  />
                </Col>

                {/* Quality Slider */}
                <Col xs={24} sm={12}>
                  <div style={{ marginBottom: 4 }}>
                    <Text>图片质量: {quality}%</Text>
                  </div>
                  <Slider
                    min={1}
                    max={100}
                    value={quality}
                    onChange={setQuality}
                    tooltip={{ formatter: (value) => `${value}%` }}
                  />
                </Col>
              </Row>
            </div>

            <Divider style={{ margin: "16px 0" }} />

            {/* Action Buttons */}
            <Row gutter={12}>
              <Col flex="auto">
                <Button
                  type="primary"
                  icon={isConverting ? <SyncOutlined spin /> : <SyncOutlined />}
                  onClick={handleConvert}
                  disabled={isConverting || inputFiles.length === 0 || (!useSourceDir && !outputDir)}
                  loading={isConverting}
                  block
                >
                  {isConverting ? "转换中..." : "开始转换"}
                </Button>
              </Col>
              <Col>
                <Button
                  danger
                  icon={<ReloadOutlined />}
                  onClick={handleReset}
                  disabled={isConverting}
                >
                  重置
                </Button>
              </Col>
            </Row>

            {/* Results */}
            {result && (
              <>
                <Divider style={{ margin: "16px 0" }} />
                <Alert
                  message={
                    <Space size="small">
                      {result.success ? (
                        <CheckCircleOutlined />
                      ) : (
                        <CloseCircleOutlined />
                      )}
                      <Text strong>
                        {result.success ? "转换完成！" : "转换失败"}
                      </Text>
                    </Space>
                  }
                  type={result.success ? "success" : "error"}
                  showIcon={false}
                  style={{ marginBottom: 12 }}
                />

                <Row gutter={12}>
                  <Col span={8}>
                    <Card size="small" bodyStyle={{ padding: "16px" }}>
                      <Statistic
                        title="总文件数"
                        value={result.total}
                        valueStyle={{ color: "#1890ff", fontSize: 24 }}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" bodyStyle={{ padding: "16px" }}>
                      <Statistic
                        title="成功转换"
                        value={result.converted}
                        valueStyle={{ color: "#52c41a", fontSize: 24 }}
                        prefix={<CheckCircleOutlined />}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card size="small" bodyStyle={{ padding: "16px" }}>
                      <Statistic
                        title="转换失败"
                        value={result.failed}
                        valueStyle={{ color: result.failed > 0 ? "#ff4d4f" : "#52c41a", fontSize: 24 }}
                        prefix={result.failed > 0 ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
                      />
                    </Card>
                  </Col>
                </Row>

                {result.errors.length > 0 && (
                  <Card
                    title="错误详情"
                    size="small"
                    bodyStyle={{ padding: "12px" }}
                    style={{ marginTop: 12, maxHeight: 180, overflow: "auto" }}
                  >
                    <List
                      size="small"
                      split={false}
                      dataSource={result.errors}
                      renderItem={(error) => (
                        <List.Item style={{ padding: "4px 0", border: "none" }}>
                          <Text type="danger" style={{ fontSize: 13 }}>• {error}</Text>
                        </List.Item>
                      )}
                    />
                  </Card>
                )}
              </>
            )}
          </Space>
        </Card>

        {/* Footer */}
        <div style={{ textAlign: "center", marginTop: 16 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            使用 Rust + Tauri + React + Ant Design 构建
          </Text>
        </div>
      </div>
    </div>
  );
}

export default App;
