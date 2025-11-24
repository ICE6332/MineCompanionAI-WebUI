"use client";

import { useRef } from "react";
import {
  Cropper,
  CircleStencil,
  CropperRef,
  ImageRestriction,
} from "react-advanced-cropper";
import "react-advanced-cropper/dist/style.css";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface AvatarCropperProps {
  isOpen: boolean;
  onClose: () => void;
  imageSrc: string;
  onCropComplete: (croppedBlob: Blob) => void;
}

export function AvatarCropper({
  isOpen,
  onClose,
  imageSrc,
  onCropComplete,
}: AvatarCropperProps) {
  const cropperRef = useRef<CropperRef>(null);

  const handleCrop = () => {
    const canvas = cropperRef.current?.getCanvas();
    if (!canvas) return;

    const size = Math.min(canvas.width, canvas.height);
    const output = document.createElement("canvas");
    output.width = size;
    output.height = size;

    const ctx = output.getContext("2d");
    if (!ctx) return;

    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
    ctx.closePath();
    ctx.clip();
    ctx.drawImage(canvas, 0, 0, size, size);

    output.toBlob(
      (blob: Blob | null) => {
        if (blob) {
          onCropComplete(blob);
          onClose();
        }
      },
      "image/png",
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>头像裁剪</DialogTitle>
          <DialogDescription>拖动、缩放以微调头像。</DialogDescription>
        </DialogHeader>
        <div className="relative w-full h-[400px] bg-black/5 rounded-md overflow-hidden">
          <Cropper
            ref={cropperRef}
            src={imageSrc}
            stencilComponent={CircleStencil}
            stencilProps={{
              aspectRatio: 1,
              resizable: false,
              movable: false,
              overlayClassName: "bg-black/50",
            }}
            className="h-full w-full"
            imageRestriction={ImageRestriction.stencil}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleCrop}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
