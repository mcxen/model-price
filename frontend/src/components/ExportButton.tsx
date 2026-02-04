import type { ModelPricing } from '../types/pricing';
import { getProviderDisplayName } from '../config';

interface ExportButtonProps {
  models: ModelPricing[];
}

const EXPORT_COLUMNS = [
  '提供商',
  '模型ID',
  '模型名称',
  '输入价格($/M)',
  '输出价格($/M)',
  '缓存输入($/M)',
  '缓存写入($/M)',
  '推理价格($/M)',
  '图像输入($/M)',
  '音频输入($/M)',
  '音频输出($/M)',
  'Embedding($/M)',
  '批量输入($/M)',
  '批量输出($/M)',
  '上下文长度',
  '最大输出',
  '开源',
  '能力',
  '输入模态',
  '输出模态',
  '更新时间',
] as const;

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatCell(value: string | number | boolean | null | undefined): string {
  if (value === null || value === undefined) return '';
  return escapeHtml(String(value));
}

function buildTableRows(models: ModelPricing[]): string {
  return models
    .map((model) => {
      const isOpenSource = model.is_open_source === null
        ? '未知'
        : model.is_open_source
          ? '开源'
          : '闭源';

      const cells = [
        getProviderDisplayName(model.provider),
        model.model_id,
        model.model_name,
        model.pricing.input,
        model.pricing.output,
        model.pricing.cached_input,
        model.pricing.cached_write,
        model.pricing.reasoning,
        model.pricing.image_input,
        model.pricing.audio_input,
        model.pricing.audio_output,
        model.pricing.embedding,
        model.batch_pricing?.input ?? null,
        model.batch_pricing?.output ?? null,
        model.context_length,
        model.max_output_tokens,
        isOpenSource,
        model.capabilities.join(', '),
        model.input_modalities.join(', '),
        model.output_modalities.join(', '),
        model.last_updated,
      ];

      return `<tr>${cells.map((cell) => `<td>${formatCell(cell)}</td>`).join('')}</tr>`;
    })
    .join('');
}

function buildExcelHtml(models: ModelPricing[]): string {
  const headerRow = EXPORT_COLUMNS
    .map((column) => `<th>${escapeHtml(column)}</th>`)
    .join('');
  const bodyRows = buildTableRows(models);

  return `<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office"
      xmlns:x="urn:schemas-microsoft-com:office:excel"
      xmlns="http://www.w3.org/TR/REC-html40">
  <head>
    <meta charset="UTF-8" />
    <style>
      table { border-collapse: collapse; font-family: Arial, sans-serif; font-size: 12px; }
      th, td { border: 1px solid #d1d5db; padding: 6px 8px; }
      th { background: #f3f4f6; font-weight: 600; }
    </style>
  </head>
  <body>
    <table>
      <thead><tr>${headerRow}</tr></thead>
      <tbody>${bodyRows}</tbody>
    </table>
  </body>
</html>`;
}

function buildFileName(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, '0');
  const datePart = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}`;
  const timePart = `${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
  return `model-price-${datePart}-${timePart}.xls`;
}

export function ExportButton({ models }: ExportButtonProps) {
  const handleExport = () => {
    if (models.length === 0) return;

    const html = buildExcelHtml(models);
    const blob = new Blob(['\ufeff', html], {
      type: 'application/vnd.ms-excel;charset=utf-8;',
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = buildFileName();
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <button
      className="export-btn"
      onClick={handleExport}
      disabled={models.length === 0}
      title={models.length === 0 ? '暂无可导出的结果' : '导出当前筛选结果为 Excel'}
    >
      <span className="export-icon">⇩</span>
      <span className="export-text">导出Excel</span>
    </button>
  );
}
