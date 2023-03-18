from collections.abc import Collection, Iterable, Mapping, Set
from dataclasses import dataclass, field
from grp import getgrnam
from itertools import chain
from os import PathLike
from os import chown as os_chown
from os import walk as os_walk
from os.path import join as path_join
from pathlib import Path, PurePath
from platform import python_version_tuple
from pwd import getpwnam
from shutil import copytree
from shutil import move as sh_move
from shutil import rmtree
from subprocess import Popen, SubprocessError
from subprocess import run as sp_run
from tempfile import mkdtemp
from typing import Any, Final, NamedTuple, Optional, Union
from uuid import uuid4


_PYTHON_VERSION = tuple(map(int, python_version_tuple()))
if _PYTHON_VERSION >= (3, 10):
    from typing import TypeAlias  # type: ignore[misc,attr-defined]

    PathRep: TypeAlias  # type: ignore[valid-type]

PathRep = Union[str, PathLike]


def shred_dir(directory: PathRep, shred_options: Iterable[str] = tuple()) -> None:
    """
    Shreds all files and subdirectories under specified directory to prevent
    leakage of sensitive data, as a simple ``rm -r`` or ``shutil.rmtree`` does not shred
    each individual file's content.

    :param directory: directory to shred
    :type directory: ``str | PathLike``

    :param shred_options: flags to pass to UNIX `shred` command (``-u`` is already passed.)
    :type shred_options: ``Iterable[str]``
    """

    files_to_shred: Final[list[str]] = []
    for dirpath, _, files in os_walk(directory):  # type: ignore
        files_to_shred.extend(path_join(dirpath, file) for file in files)

    if files_to_shred:
        sp_run(("shred", "-f", "-u", *shred_options, "--", *files_to_shred), check=True)
    rmtree(directory)


def _kw_only_field(*args, **kwargs):
    return field(
        *args, **kwargs, **({"kw_only": True} if _PYTHON_VERSION >= (3, 10) else {})
    )


@dataclass(init=False, frozen=True)
class Copy:
    """
    An immutable object that represents a path on the host file system to be copied to
    (a subdirectory of) a named Docker volume.
    Allows specifying desired metadata to be set once copied to the Docker volume.

    :param path: path on host file system
    :type path: ``str | PathLike``

    :param children: additional paths or ``Copy`` objects that are children of this ``Copy`` object.
        When children are copied to the Docker container, their metadata will inherit their
        parents' default metadata unless overriden.
    :type children: ``Set[Copy]``

    :param subdir: optional subdirectory of the named Docker volume to be the copy destination
    :type subdir: ``Optional[str | PathLike]``

    :param default_user_owner: Sets the copied file's user owner and
        default user owner for children in the Docker volume. If using a string name, note that
        it will be translated to a UID according to host file system, not Docker container.
    :type default_user_owner: ``Optional[int | str]``

    :param default_group_owner: Sets the copied file's user owner and
        default user owner for children in the Docker volume. If using a string name, note that
        it will be translated to a UID according to host file system, not Docker container.
    :type default_group_owner: ``Optional[int | str]``

    :param default_file_params: Argument to UNIX `chmod`. If specified and ``path`` is a file,
        then just the file's permissions will be modified. If ``path`` is a directory,
        all children files' permissions will be modified as such unless those children files or
        their directory parents override this value for themselves.
    :type default_file_params: ``Optional[str]``

    :param default_dir_params: Argument to UNIX `chmod`. If specified and ``path`` is a directory,
        then the permissions of the directory and all children directories will be modified
        (unless those children directories or their directory parents
        override this value for themselves).
    :type default_dir_params: ``Optional[str]``

    """

    path: Path
    children: frozenset["Copy"] = frozenset()  # type: ignore
    subdir: Optional[PurePath] = None
    default_user_owner: Optional[int] = _kw_only_field(default=None, compare=False)
    default_group_owner: Optional[int] = _kw_only_field(default=None, compare=False)
    default_file_perms: Optional[str] = _kw_only_field(default=None, compare=False)
    default_dir_perms: Optional[str] = _kw_only_field(default=None, compare=False)

    def __init__(
        self,
        path: PathRep,
        /,
        children: frozenset["Copy"] = frozenset(),
        subdir: Optional[PathRep] = None,
        *,
        default_user_owner: Optional[Union[int, str]] = None,
        default_group_owner: Optional[Union[int, str]] = None,
        default_file_perms: Optional[str] = None,
        default_dir_perms: Optional[str] = None,
    ):
        if not isinstance(path, Path):
            path = Path(path)
        if path.is_file() and children:
            raise ValueError("Cannot have any children if file itself")

        if subdir is not None:
            if not isinstance(subdir, PurePath):
                subdir = PurePath(subdir)
            if subdir.is_absolute():
                raise ValueError(f"{subdir=!r} cannot be an absolute path")

        if isinstance(default_file_perms, str) and default_file_perms in ("", "--"):
            raise ValueError(
                f"{default_file_perms=!r} must be a valid argument to UNIX chmod"
            )

        if isinstance(default_dir_perms, str) and default_dir_perms in ("", "--"):
            raise ValueError(
                f"{default_dir_perms=!r} must be a valid argument to UNIX chmod"
            )

        if isinstance(default_user_owner, str):
            default_user_owner = getpwnam(default_user_owner).pw_uid
        if isinstance(default_group_owner, str):
            default_group_owner = getgrnam(default_group_owner).gr_gid

        object.__setattr__(self, "path", path)
        object.__setattr__(self, "children", children)
        object.__setattr__(self, "subdir", subdir)
        object.__setattr__(self, "default_user_owner", default_user_owner)
        object.__setattr__(self, "default_group_owner", default_group_owner)
        object.__setattr__(self, "default_file_perms", default_file_perms)
        object.__setattr__(self, "default_dir_perms", default_dir_perms)

    @classmethod
    def in_(
        cls,
        directory: Union[PathRep, "Copy"],
        /,
        subdir: Optional[PathRep] = None,
        *,
        default_user_owner: Optional[Union[int, str]] = None,
        default_group_owner: Optional[Union[int, str]] = None,
        default_file_perms: Optional[str] = None,
        default_dir_perms: Optional[str] = None,
    ) -> frozenset["Copy"]:
        as_path: Final[Path] = (
            directory.path if isinstance(directory, Copy) else Path(directory)
        )

        return frozenset(
            cls(
                child,
                subdir=subdir,
                default_user_owner=default_user_owner,
                default_group_owner=default_group_owner,
                default_file_perms=default_file_perms,
                default_dir_perms=default_dir_perms,
            )
            for child in as_path.iterdir()
        )

    def _changes_user_owner(self) -> bool:
        return any(child._changes_user_owner() for child in self.children) or (
            self.default_user_owner is not None
            and self.path.stat().st_uid != self.default_user_owner
        )

    def _changes_group_owner(self) -> bool:
        return any(child._changes_group_owner() for child in self.children) or (
            self.default_group_owner is not None
            and self.path.stat().st_gid != self.default_group_owner
        )

    def _may_change_perms(self) -> bool:
        return (
            any(child._may_change_perms() for child in self.children)
            or self.default_file_perms is not None
            or (self.path.is_dir() and self.default_dir_perms is not None)
        )

    def _children_have_custom_subdir(self) -> bool:
        return any(child.subdir is not None for child in self.children)

    def artificial(self) -> bool:
        """
        Returns whether the represented path must be copied to a temporary directory or not,
        taking into account the user/group owner or permissions that the files should
        have inside the Docker volume once copied. A ``False`` value means that
        it is safe to mount the path directly in the Docker container that facilitates
        the copying.
        """
        return (
            self._changes_user_owner()
            or self._changes_group_owner()
            or self._may_change_perms()
            or self._children_have_custom_subdir()
        )

    def set_metadata(
        self,
        output_dir: Path,
        parent_dir: Optional[Path] = None,
        *,
        default_user_owner: Optional[int] = None,
        default_group_owner: Optional[int] = None,
        default_file_perms: Optional[str] = None,
        default_dir_perms: Optional[str] = None,
    ) -> None:
        """
        Sets all desired metadata (user/group owner, permissions) to all appropriate
        files/directories in the output directory relative to the original root path.

        :param output_dir: The output directory that represents the root ``Copy`` object.
            Recursive calls of this function hold this parameter constant.
        :type output_dir: ``Path``

        :param parent_dir: The parent directory that holds the root ``Copy`` object. If
            not provided, will default to the immediate parent directory of object's `path`.
            Recursive calls of this function hold this parameter constant.
        :type parent_dir: ``Optional[Path]``


        :param default_user_owner: Self-explanatory, see ``Copy.default_user_owner``
        :type default_user_owner: ``Optional[int]``

        :param default_group_owner: Self-explanatory, see ``Copy.default_group_owner``
        :type default_group_owner: ``Optional[int]``

        :param default_file_perms: Self-explanatory, see ``Copy.default_file_perms``
        :type default_file_perms: ``Optional[str]``

        :param default_dir_perms: Self-explanatory, see ``Copy.default_dir_perms``
        :type default_dir_perms: ``Optional[str]``

        """
        if parent_dir is None:
            parent_dir = self.path.parent

        relative_path: PurePath = self.path.relative_to(parent_dir)
        parent_dir /= relative_path
        if self.subdir is not None:
            (output_dir / self.subdir).mkdir(parents=True)
            sh_move(output_dir / relative_path, output_dir / self.subdir)
            relative_path = self.subdir / self.path.name

        output_dir /= relative_path

        if self.default_user_owner is not None:
            default_user_owner = self.default_user_owner
        if self.default_group_owner is not None:
            default_group_owner = self.default_group_owner
        if self.default_file_perms is not None:
            default_file_perms = self.default_file_perms
        if self.default_dir_perms is not None:
            default_dir_perms = self.default_dir_perms

        if not (default_user_owner is None and default_group_owner is None):
            uid: Final[int] = -1 if default_user_owner is None else default_user_owner
            gid: Final[int] = -1 if default_group_owner is None else default_group_owner
            if output_dir.is_dir():
                for dirpath, _, files in os_walk(output_dir):
                    os_chown(dirpath, uid, gid, follow_symlinks=False)
                    for file in files:
                        os_chown(
                            path_join(dirpath, file), uid, gid, follow_symlinks=False
                        )
                del dirpath, files
            else:
                os_chown(output_dir, uid, gid, follow_symlinks=False)

        if not (default_file_perms is None and default_dir_perms is None):
            if output_dir.is_dir():
                file_list: Final[list[str]] = []
                dir_list: Final[list[str]] = []
                for dirpath, _, files in os_walk(output_dir):
                    if default_file_perms is not None:
                        file_list.extend(path_join(dirpath, file) for file in files)
                    if default_dir_perms is not None:
                        dir_list.append(dirpath)
                del dirpath, files

                if default_file_perms is not None:
                    sp_run(("chmod", default_file_perms, "--", *file_list), check=True)
                if default_dir_perms is not None:
                    sp_run(("chmod", default_dir_perms, "--", *dir_list), check=True)
            elif default_file_perms is not None:
                sp_run(("chmod", default_file_perms, "--", str(output_dir)), check=True)

        for child in self.children:
            child.set_metadata(
                output_dir,
                parent_dir,
                default_user_owner=default_user_owner,
                default_group_owner=default_group_owner,
                default_file_perms=default_file_perms,
                default_dir_perms=default_dir_perms,
            )


class _VolDir(NamedTuple):
    name: str
    path: Path
    is_temp: bool = field(compare=False)

    @staticmethod
    def get_dirs(
        cls,
        volumes: Mapping[str, Set[Copy]],
        mkdtemp_opts: Mapping[str, Any] = {},
        *args,
        **kwargs,
    ) -> Set["_VolDir"]:
        """
        Returns a list of directories that can be directly copied to the Docker volume after
        copying file structures to temporary directories and setting up desired
        file structures, metadata, etc. if necessary.
        """
        vol_dirs: Final[set["_VolDir"]] = set()
        try:
            for vol, copyobjs in volumes.items():
                if len(copyobjs) == 0:
                    continue

                parents: frozenset[Path] = frozenset(
                    copyobj.path.parent for copyobj in copyobjs
                )
                is_temp: bool = len(parents) > 1 or any(
                    copyobj.artificial() for copyobj in copyobjs
                )

                holding_dir: Path
                if is_temp:
                    holding_dir = Path(mkdtemp(**mkdtemp_opts))
                    try:
                        for copyobj in copyobjs:
                            output_dir: Path = (
                                holding_dir
                                if copyobj.subdir is None
                                else holding_dir / copyobj.subdir
                            )
                            copytree(copyobj.path, output_dir / copyobj.path.name)
                            copyobj.set_metadata(output_dir, *args, **kwargs)
                    except:
                        shred_dir(holding_dir)
                else:
                    holding_dir = next(iter(parents))

                vol_dirs.add(cls(vol, holding_dir, is_temp))

            return vol_dirs
        except:
            for _, vol_dir, is_temp in vol_dirs:
                if is_temp:
                    shred_dir(vol_dir)
            raise


def copy_to_volume(
    volumes: Mapping[str, Union[PathLike, Copy, Set[Union[PathLike, Copy]]]],
    image: str = "hello-world",
    *args,
    **kwargs,
) -> None:
    """
    Takes a dictionary mapping Docker volume names to a number of files or directories
    that will be copied to their corresponding volume while preserving file structure and
    respecting desired metadata.

    :param volumes: Mapping from Docker volume name to a single or non-empty collection of
        paths as strings or``Path``s or ``Copy`` objects.
    :type volumes: ``Mapping[str, Union[PathLike, Copy, Collection[Union[PathLike, Copy]]``

    :param image: Docker image to use, uses ``"hello-world"`` by default. ``busybox:musl``
        is not a bad choice if some core utilities are needed.
    :type image: ``str``

    Extraneous arguments are passed to calls to ``Copy.set_metadata`` for each ``Copy`` object.
    """

    volumes_tmp: Final[dict[str, frozenset[Copy]]] = {}

    for volume_name, paths in volumes.items():
        if isinstance(paths, (PathLike, Copy)):
            paths = (paths,)  # type: ignore[assignment]
        volumes_tmp[volume_name] = frozenset(
            path if isinstance(path, Copy) else Copy(path) for path in paths  # type: ignore[union-attr]
        )
    volumes = volumes_tmp

    vol_dirs: Collection[_VolDir] = _VolDir.get_dirs(volumes, *args, **kwargs)

    try:
        container_name: Final[str] = str(uuid4())

        sp_run(
            (
                "docker",
                "container",
                "create",
                "-d",
                "--rm",
                "--name",
                container_name,
                *chain(
                    *(("-v", f"{vol_dir}:/mnt/{vol}") for vol, vol_dir, *_ in vol_dirs)
                ),
                image,
            ),
            check=True,
        )

        try:
            processes: Final[list[Popen]] = []

            for vol, vol_dir, *_ in vol_dirs:
                processes.append(
                    Popen(
                        (
                            "docker",
                            "cp",
                            f"{vol_dir}/.",
                            f"{container_name}:/mnt/{vol}",
                        )
                    )
                )

            copy_error: int = 0
            for process in processes:
                copy_error = max(copy_error, process.wait())

            if copy_error:
                raise SubprocessError("docker copy function failed")
        finally:
            sp_run(("docker", "rm", container_name), check=True)

    finally:
        for _, vol_dir, is_temp in vol_dirs:
            if is_temp:
                shred_dir(vol_dir)
