# coding=utf8
import sublime
import sublime_plugin
import os
import threading
import shutil

class SideBarCommand(sublime_plugin.WindowCommand):

	def copy_to_clipboard_and_inform(self, data):
		sublime.set_clipboard(data)
		self.window.status_message('copied "{}" to clipboard'.format(data))

	def get_path(self, paths):
		try:
			return paths[0]
		except IndexError:
			return self.window.active_view().file_name()

class SideBarCopyNameCommand(SideBarCommand):

	def run(self, paths):
		path = self.get_path(paths)
		name = os.path.split(path)[1]
		self.copy_to_clipboard_and_inform(name)

	def description(self):
		return 'Copy Filename'

class SideBarCopyAbsolutePathCommand(SideBarCommand):

	def run(self, paths):
		path = self.get_path(paths)
		self.copy_to_clipboard_and_inform(path)

	def description(self):
		return 'Copy Absolute Path'

class SideBarCopyRelativePathCommand(SideBarCommand):

	def run(self, paths):
		path = self.get_path(paths)
		project_file_name = self.window.project_file_name()
		root_dir = ''
		if project_file_name:
			root_dir = os.path.dirname(project_file_name)
		else:
			root_dir = self.window.project_data()['folders'][0]['path']
		common = os.path.commonprefix([root_dir, path])
		path = path[len(common):]
		if path.startswith('/') or path.startswith('\\'):
			path = path[1:]
		self.copy_to_clipboard_and_inform(path)

	def description(self):
		return 'Copy Relative Path'

class SideBarDuplicateCommand(SideBarCommand):

	def run(self, paths):
		self.view = self.window.active_view()
		self.source = self.get_path(paths)
		base, leaf = os.path.split(self.source)
		name, ext = os.path.splitext(leaf)
		initial_text = name + ' (Copy)' + ext
		input_panel = self.window.show_input_panel('Duplicate As:',
			initial_text, self.on_done, None, None)

		input_panel.sel().clear()
		input_panel.sel().add(sublime.Region(0, len(initial_text) - (len(ext))))

	def on_done(self, destination):
		base, _ = os.path.split(self.source)
		destination = os.path.join(base, destination)
		threading.Thread(target=self.copy,
			args=(self.source, destination)).start()

	def copy(self, source, destination):
		print(source, destination)
		if self.view:
			self.view.set_status('SideBarTools:Copy', 'copying "{}" to "{}"'.format(
				source, destination))
		else:
			self.window.status_message('copying "{}" to "{}"'.format(
				source, destination))

		if os.path.isdir(source):
			shutil.copytree(source, destination)
		else:
			shutil.copy2(source, destination)

		if self.view:
			self.view.erase_status('SideBarTools:Copy')

	def description(self):
		return 'Duplicate File…'


def temporary_status_message(view, message, key='SideBarTools', duration=5000):
	view.set_status(key, message)

	def erase_status():
		view.erase_status(key)

	sublime.set_timeout_async(erase_status, duration)


class SideBarMoveCommand(SideBarCommand):

	def run(self, paths):
		self.view = self.window.active_view()
		self.source = self.get_path(paths)

		input_panel = self.window.show_input_panel(
			'Move to:', self.source, self.on_done, None, None)

		base, leaf = os.path.split(self.source)
		name, ext = os.path.splitext(leaf)

		input_panel.sel().clear()
		input_panel.sel().add(sublime.Region(len(base) + 1, len(self.source) - len(ext)))

	def on_done(self, destination):
		threading.Thread(target=self.move, args=(self.source, destination)).start()

	def move(self, source, destination):
		print(source, destination)
		if self.view:
			self.view.set_status(
				'SideBarTools:Move', 'Moving "{}" to "{}"'.format(source, destination))
		else:
			self.window.status_message(
				'Moving "{}" to "{}"'.format(source, destination))

		destination_dir = os.path.dirname(destination)
		try:
			os.makedirs(destination_dir)
		except OSError:
			print('Destination directory seems to exists...')

		if self.view:
			self.view.erase_status('SideBarTools:Move')

		try:
			shutil.move(source, destination)
		except OSError as error:
			message = 'Error moving "{src}" to "{dst}": {error}'.format(
				src=source,
				dst=destination,
				error=error,
			)
			if self.view:
				temporary_status_message(
					self.view,
					message,
					key='SideBarTools:Move'
				)
			else:
				print(message)

	def description(self):
		return 'Move File…'
