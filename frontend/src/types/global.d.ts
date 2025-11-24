/// <reference types="react" />
/// <reference types="react-dom" />

// 兼容遗留引用，避免开发时类型缺失导致报错
declare module "react-cropper" {
  const ReactCropper: any;
  export default ReactCropper;
}
