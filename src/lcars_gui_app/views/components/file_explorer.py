"""File explorer panel for the LCARS GUI application."""

from PySide6.QtCore import QDir
from PySide6.QtWidgets import QFileSystemModel, QTreeView, QVBoxLayout, QWidget


class FileExplorerPanel(QWidget):
    """Declarative UI component leveraging Qt's built in filesystem model."""

    def __init__(self):
        """Initialize the file explorer panel with a tree view of the filesystem."""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # instantiate the model
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())

        # instantiate the view and bind the Model
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.rootPath()))

        # apply baseline LCARS styling (can be moved to constants later)
        self.tree_view.setStyleSheet("""
            QTreeView {
                background-color: #000000;
                color: #FF9900;
                font-size: 16px;
                border: 2px solid #CC6699;
            }
        """)

        layout.addWidget(self.tree_view)


# This was built by referencing the following Qt documentation:
# QFileSystemModel, find it here:
# https://doc.qt.io/qtforpython-6/PySide6/QtGui/QFileSystemModel.html
# QTreeView integration with models, find it here:
# https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTreeView.html
