module Download {
  interface Intermediary {
    string downloadTask(string url);
  };

  interface Downloader {
    string addDownloadTask(string url);
  };
};
