export interface AssetItem {
  id: string;
  name: string;
  type: 'DATASET' | 'MODEL';
  format: string;
  size: string;
  hash: string;
  registeredAt: string;
  status: 'READY' | 'NOT_READY' | 'ERROR';
}
