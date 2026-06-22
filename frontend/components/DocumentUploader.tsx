'use client';

import React, { useState } from 'react';
import { toast } from 'react-toastify';

interface DocumentUploaderProps {
  sessionId: string;
}

interface IngestResponse {
  chunks_indexed: number;
}

const DocumentUploader: React.FC<DocumentUploaderProps> = ({ sessionId }) => {
  const [uploading, setUploading] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [chunksIndexed, setChunksIndexed] = useState<number | null>(null);

  const handleFileUpload = async (file: File) => {
    if (!file || !sessionId) {
      toast.error('Invalid file or session ID.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    try {
      setUploading(true);
      setProgress(0);

      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/ai/ingest', true);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          setProgress(percentComplete);
        }
      };

      xhr.onload = () => {
        setUploading(false);
        if (xhr.status === 200) {
          const response: IngestResponse = JSON.parse(xhr.responseText);
          setChunksIndexed(response.chunks_indexed);
          toast.success(`Successfully indexed ${response.chunks_indexed} chunks.`);
        } else {
          const errorResponse = JSON.parse(xhr.responseText);
          toast.error(errorResponse.message || 'Failed to upload file.');
        }
      };

      xhr.onerror = () => {
        setUploading(false);
        toast.error('An error occurred during file upload.');
      };

      xhr.send(formData);
    } catch (error) {
      setUploading(false);
      toast.error('An unexpected error occurred.');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  return (
    <div
      className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center cursor-pointer"
      onDragOver={(event) => event.preventDefault()}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept=".xlsx,.xls,.pdf,.docx"
        className="hidden"
        id="file-upload"
        onChange={handleFileSelect}
      />
      <label htmlFor="file-upload" className="block text-gray-600">
        Drag and drop a file here or <span className="text-blue-500 underline">browse</span>
      </label>
      {uploading && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-500 h-4 rounded-full"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-2">{progress}% uploaded</p>
        </div>
      )}
      {chunksIndexed !== null && (
        <div className="mt-4">
          <span className="bg-green-500 text-white px-2 py-1 rounded-full">
            ✓ Indexed {chunksIndexed} chunks
          </span>
        </div>
      )}
    </div>
  );
};

export default DocumentUploader;