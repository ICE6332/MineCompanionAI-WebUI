'use client';

import { Dropzone, DropzoneContent, DropzoneEmptyState } from '@/components/ui/shadcn-io/dropzone';
import { useState, useEffect } from 'react';
import { AvatarCropper } from './avatar-cropper';

interface AvatarUploadProps {
    value?: string;
    onChange?: (file: File) => void;
}

const AvatarUpload = ({ value, onChange }: AvatarUploadProps) => {
    const [files, setFiles] = useState<File[] | undefined>();
    const [filePreview, setFilePreview] = useState<string | undefined>(value);
    const [isCropperOpen, setIsCropperOpen] = useState(false);
    const [imageToCrop, setImageToCrop] = useState<string | null>(null);

    useEffect(() => {
        if (value) {
            setFilePreview(value);
        }
    }, [value]);

    const handleDrop = (droppedFiles: File[]) => {
        if (droppedFiles.length > 0) {
            const file = droppedFiles[0];
            const reader = new FileReader();
            reader.onload = (e) => {
                if (typeof e.target?.result === 'string') {
                    setImageToCrop(e.target.result);
                    setIsCropperOpen(true);
                }
            };
            reader.readAsDataURL(file);
        }
    };

    const handleCropComplete = (croppedBlob: Blob) => {
        const croppedFile = new File([croppedBlob], 'avatar.png', { type: 'image/png' });
        const previewUrl = URL.createObjectURL(croppedBlob);

        setFilePreview(previewUrl);
        setFiles([croppedFile]);

        if (onChange) {
            onChange(croppedFile);
        }
    };

    return (
        <>
            <Dropzone
                accept={{ 'image/*': ['.png', '.jpg', '.jpeg'] }}
                onDrop={handleDrop}
                onError={console.error}
                src={files}
                className="h-[102px] w-[102px] rounded-full overflow-hidden border-2 border-dashed border-muted-foreground/25 hover:border-muted-foreground/50 transition-colors p-0"
            >
                <DropzoneEmptyState className="p-0">
                    <div className="flex items-center justify-center h-full w-full text-xs text-muted-foreground font-medium">
                        Avatar
                    </div>
                </DropzoneEmptyState>
                <DropzoneContent className="h-full w-full p-0 flex items-center justify-center">
                    {filePreview ? (
                        <img
                            alt="Preview"
                            className="h-full w-full object-cover"
                            src={filePreview}
                        />
                    ) : (
                        <div className="text-xs text-muted-foreground text-center p-2">
                            Avatar
                        </div>
                    )}
                </DropzoneContent>
            </Dropzone>

            {imageToCrop && (
                <AvatarCropper
                    isOpen={isCropperOpen}
                    onClose={() => setIsCropperOpen(false)}
                    imageSrc={imageToCrop}
                    onCropComplete={handleCropComplete}
                />
            )}
        </>
    );
};

export default AvatarUpload;
