//! OS-exclusive Resident lock boundary.

use std::fs::{File, OpenOptions};
use std::path::Path;

use fs4::{FileExt, TryLockError};

use super::ResidentError;

pub(crate) struct ResidentLock {
    file: File,
    held: bool,
}

impl ResidentLock {
    pub(crate) fn acquire(path: impl AsRef<Path>) -> Result<Self, ResidentError> {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(path)
            .map_err(ResidentError::LockIo)?;
        Self::acquire_file(file)
    }

    pub(crate) fn acquire_file(file: File) -> Result<Self, ResidentError> {
        match FileExt::try_lock(&file) {
            Ok(()) => Ok(Self { file, held: true }),
            Err(TryLockError::WouldBlock) => Err(ResidentError::LockUnavailable),
            Err(TryLockError::Error(error)) => Err(ResidentError::LockIo(error)),
        }
    }

    pub(crate) fn release(mut self) -> Result<(), ResidentError> {
        self.release_inner()
    }

    fn release_inner(&mut self) -> Result<(), ResidentError> {
        if self.held {
            FileExt::unlock(&self.file).map_err(ResidentError::LockIo)?;
            self.held = false;
        }
        Ok(())
    }
}

impl Drop for ResidentLock {
    fn drop(&mut self) {
        let _ = self.release_inner();
    }
}

#[cfg(test)]
mod tests {
    use std::process::Command;

    use super::*;

    const CHILD_ENV: &str = "AGENTS_OS_WP2_LOCK_CHILD";
    const PATH_ENV: &str = "AGENTS_OS_WP2_LOCK_PATH";

    #[test]
    fn subprocess_lock_probe() {
        if std::env::var_os(CHILD_ENV).is_none() {
            return;
        }
        let path = std::env::var_os(PATH_ENV).expect("child lock path");
        assert!(matches!(
            ResidentLock::acquire(Path::new(&path)),
            Err(ResidentError::LockUnavailable)
        ));
    }

    #[test]
    fn exclusive_lock_rejects_a_second_process() {
        let root = tempfile::tempdir().expect("temporary synthetic root");
        let path = root.path().join("resident.lock");
        let lock = ResidentLock::acquire(&path).expect("parent lock");
        let status = Command::new(std::env::current_exe().expect("test executable"))
            .arg("--exact")
            .arg("resident::lock::tests::subprocess_lock_probe")
            .arg("--nocapture")
            .env(CHILD_ENV, "1")
            .env(PATH_ENV, &path)
            .status()
            .expect("child process");
        assert!(status.success(), "child must observe the held OS lock");
        lock.release().expect("release lock");
    }
}
