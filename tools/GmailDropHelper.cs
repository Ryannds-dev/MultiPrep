using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows.Forms;

internal static class Program
{
    [DllImport("user32.dll")]
    private static extern IntPtr SetParent(IntPtr child, IntPtr parent);

    [DllImport("user32.dll")]
    private static extern bool GetClientRect(IntPtr window, out RECT rect);

    [DllImport("user32.dll")]
    private static extern bool MoveWindow(IntPtr window, int x, int y, int width, int height, bool repaint);

    [DllImport("user32.dll")]
    private static extern short GetAsyncKeyState(int virtualKey);

    [DllImport("user32.dll")]
    private static extern bool GetCursorPos(out POINT point);

    [DllImport("user32.dll")]
    private static extern bool ClientToScreen(IntPtr window, ref POINT point);

    [DllImport("user32.dll")]
    private static extern IntPtr GetAncestor(IntPtr window, uint flags);

    [DllImport("user32.dll")]
    private static extern bool GetWindowRect(IntPtr window, out RECT rect);

    [StructLayout(LayoutKind.Sequential)]
    private struct RECT
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct POINT
    {
        public int X;
        public int Y;
    }

    [ComImport]
    [Guid("3D8B0590-F691-11d2-8EA9-006097DF5BD4")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IDataObjectAsyncCapability
    {
        void SetAsyncMode(int value);
        void GetAsyncMode(out int value);
        void StartOperation(IntPtr reserved);
        void InOperation(out int value);
        void EndOperation(int result, IntPtr reserved, uint effects);
    }

    [STAThread]
    private static void Main(string[] args)
    {
        if (args.Length != 4) return;
        long parentValue;
        if (!Int64.TryParse(args[2], out parentValue)) return;
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new DropForm(args[0], args[1], new IntPtr(parentValue), args[3] == "1"));
    }

    private sealed class DropForm : Form
    {
        private readonly string outputDirectory;
        private readonly string manifestPath;
        private readonly Label label;
        private readonly IntPtr parentWindow;
        private readonly bool initiallyVisible;
        private readonly Timer cursorTimer;
        private bool dragStartedOutsideApplication;
        private bool leftWasPressed;
        private bool cursorWasInsideApplication;

        internal DropForm(string outputDirectory, string manifestPath, IntPtr parentWindow, bool initiallyVisible)
        {
            this.outputDirectory = outputDirectory;
            this.manifestPath = manifestPath;
            this.parentWindow = parentWindow;
            this.initiallyVisible = initiallyVisible;
            Text = "MultiPrep 2.0 · Dépôt Gmail";
            StartPosition = FormStartPosition.Manual;
            ShowInTaskbar = false;
            TopMost = false;
            KeyPreview = true;
            AllowDrop = true;
            BackColor = System.Drawing.Color.FromArgb(255, 253, 247);
            FormBorderStyle = FormBorderStyle.None;
            label = new Label {
                Dock = DockStyle.Fill,
                TextAlign = System.Drawing.ContentAlignment.MiddleCenter,
                Font = new System.Drawing.Font("Segoe UI Semibold", 10),
                ForeColor = System.Drawing.Color.FromArgb(32, 33, 36),
                BackColor = System.Drawing.Color.FromArgb(255, 247, 214),
                BorderStyle = BorderStyle.FixedSingle,
                Margin = new Padding(20),
                Text = "GLISSEZ LES PIÈCES JOINTES GMAIL ICI\r\nPDF · Word · JPG · PNG"
            };
            var container = new Panel {
                Dock = DockStyle.Fill,
                Padding = new Padding(4),
                BackColor = System.Drawing.Color.FromArgb(255, 253, 247)
            };
            container.Controls.Add(label);
            Controls.Add(container);
            DragEnter += OnDragEnter;
            DragDrop += OnDragDrop;
            KeyDown += OnKeyDown;
            var contextMenu = new ContextMenuStrip();
            var pasteItem = new ToolStripMenuItem("Coller");
            pasteItem.Click += (_sender, _event) => ImportClipboard();
            contextMenu.Items.Add(pasteItem);
            ContextMenuStrip = contextMenu;
            label.ContextMenuStrip = contextMenu;
            container.ContextMenuStrip = contextMenu;
            Shown += (_sender, _event) => {
                SetParent(Handle, parentWindow);
                FillParent();
                if (!initiallyVisible) Hide();
            };
            cursorTimer = new Timer { Interval = 40 };
            cursorTimer.Tick += PollDragIntoParent;
            cursorTimer.Start();
        }

        private void FillParent()
        {
            RECT bounds;
            if (GetClientRect(parentWindow, out bounds))
                MoveWindow(Handle, 0, 0, bounds.Right - bounds.Left, bounds.Bottom - bounds.Top, true);
        }

        private void PollDragIntoParent(object sender, EventArgs e)
        {
            RECT bounds;
            RECT applicationBounds;
            POINT cursor;
            POINT origin = new POINT { X = 0, Y = 0 };
            IntPtr applicationWindow = GetAncestor(parentWindow, 2);
            if (!GetClientRect(parentWindow, out bounds) ||
                !ClientToScreen(parentWindow, ref origin) ||
                applicationWindow == IntPtr.Zero ||
                !GetWindowRect(applicationWindow, out applicationBounds) ||
                !GetCursorPos(out cursor))
                return;
            bool inside = cursor.X >= origin.X && cursor.Y >= origin.Y &&
                cursor.X < origin.X + bounds.Right && cursor.Y < origin.Y + bounds.Bottom;
            bool insideApplication =
                cursor.X >= applicationBounds.Left && cursor.Y >= applicationBounds.Top &&
                cursor.X < applicationBounds.Right && cursor.Y < applicationBounds.Bottom;
            bool leftPressed = (GetAsyncKeyState(0x01) & 0x8000) != 0;
            if (!leftPressed)
            {
                dragStartedOutsideApplication = false;
                leftWasPressed = false;
                cursorWasInsideApplication = insideApplication;
                return;
            }
            if ((!leftWasPressed && !cursorWasInsideApplication) || !insideApplication)
                dragStartedOutsideApplication = true;
            if (!Visible && inside && dragStartedOutsideApplication)
            {
                FillParent();
                Show();
                BringToFront();
            }
            leftWasPressed = true;
            cursorWasInsideApplication = insideApplication;
        }

        private void OnDragEnter(object sender, DragEventArgs e)
        {
            e.Effect = DragDropEffects.Copy;
        }

        private void OnKeyDown(object sender, KeyEventArgs e)
        {
            if (e.Control && e.KeyCode == Keys.V)
            {
                e.SuppressKeyPress = true;
                ImportClipboard();
            }
        }

        private void ImportClipboard()
        {
            try
            {
                IDataObject data = Clipboard.GetDataObject();
                string imagePath = SaveEmbeddedImage(data, outputDirectory);
                if (imagePath == null)
                    throw new InvalidOperationException("Aucune image lisible dans le presse-papiers.");
                PublishFiles(new List<string> { imagePath });
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message, "Collage impossible", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private async void OnDragDrop(object sender, DragEventArgs e)
        {
            label.Text = "Téléchargement depuis Gmail…";
            Enabled = false;
            try
            {
                List<string> files = GetFiles(e.Data);
                if (files.Count == 0)
                {
                    string imagePath = SaveEmbeddedImage(e.Data, outputDirectory);
                    if (imagePath != null)
                        files.Add(imagePath);
                }
                if (files.Count == 0)
                {
                    try
                    {
                        await TriggerBrowserDownload(e.Data);
                    }
                    catch (InvalidOperationException)
                    {
                        throw new InvalidOperationException(
                            "Le navigateur ne fournit pas le contenu de cette image à l'application.\r\n\r\n" +
                            "Pour une image placée dans le corps du mail :\r\n" +
                            "1. Copiez l'image depuis Gmail.\r\n" +
                            "2. Revenez dans MultiPrep.\r\n" +
                            "3. Utilisez Ctrl+V.\r\n\r\n" +
                            "La zone « Importer Gmail » reste prévue pour les pièces jointes."
                        );
                    }
                    files = GetFiles(e.Data);
                }
                if (files.Count == 0)
                    throw new InvalidOperationException("Le navigateur n'a remis aucun fichier.");

                PublishFiles(files);
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message, "Import Gmail impossible", MessageBoxButtons.OK, MessageBoxIcon.Error);
                Enabled = true;
                label.Text = "Réessayez de déposer la pièce jointe ici";
            }
        }

        private void PublishFiles(List<string> files)
        {
            Directory.CreateDirectory(outputDirectory);
            string temporaryManifest = manifestPath + ".tmp";
            using (var writer = new StreamWriter(temporaryManifest, false, System.Text.Encoding.UTF8))
            {
                foreach (string source in files)
                {
                    string destination;
                    if (String.Equals(
                        Path.GetDirectoryName(Path.GetFullPath(source)),
                        Path.GetFullPath(outputDirectory).TrimEnd(Path.DirectorySeparatorChar),
                        StringComparison.OrdinalIgnoreCase))
                    {
                        destination = source;
                    }
                    else
                    {
                        destination = AvailablePath(Path.Combine(outputDirectory, Path.GetFileName(source)));
                        File.Copy(source, destination, false);
                    }
                    writer.WriteLine(destination);
                }
            }
            if (File.Exists(manifestPath)) File.Delete(manifestPath);
            File.Move(temporaryManifest, manifestPath);
            Enabled = true;
            label.Text = "GLISSEZ LES PIÈCES JOINTES GMAIL ICI\r\nPDF · Word · JPG · PNG";
            Hide();
        }

        private static async Task TriggerBrowserDownload(IDataObject data)
        {
            object inner = GetField(data, "innerData");
            if (inner != null && inner.GetType().Name == "OleConverter")
                inner = GetField(inner, "innerData");
            var asyncData = inner as IDataObjectAsyncCapability;
            if (asyncData == null)
                throw new InvalidOperationException("Le transfert asynchrone du navigateur est indisponible.");

            int asyncMode;
            asyncData.GetAsyncMode(out asyncMode);
            if (asyncMode == 0)
                asyncData.SetAsyncMode(1);
            await Task.Run(() => {
                asyncData.StartOperation(IntPtr.Zero);
                data.GetData(DataFormats.FileDrop);
                asyncData.EndOperation(0, IntPtr.Zero, 1);
            });
        }

        private static List<string> GetFiles(IDataObject data)
        {
            var value = data.GetData(DataFormats.FileDrop) as string[];
            return value == null ? new List<string>() : new List<string>(value);
        }

        private static string SaveEmbeddedImage(IDataObject data, string directory)
        {
            Directory.CreateDirectory(directory);
            object bitmapValue = data.GetData(DataFormats.Bitmap, true);
            var image = bitmapValue as System.Drawing.Image;
            if (image != null)
            {
                string path = AvailablePath(Path.Combine(directory, "image_gmail.png"));
                image.Save(path, System.Drawing.Imaging.ImageFormat.Png);
                return path;
            }

            string html = data.GetData(DataFormats.Html, true) as string;
            if (!String.IsNullOrEmpty(html))
            {
                Match match = Regex.Match(
                    html,
                    @"data:image/(?<type>png|jpe?g)(?:;[^,]*)?;base64,(?<data>[A-Za-z0-9+/=\s]+)",
                    RegexOptions.IgnoreCase
                );
                if (match.Success)
                {
                    try
                    {
                        byte[] bytes = Convert.FromBase64String(Regex.Replace(match.Groups["data"].Value, @"\s", ""));
                        return SaveImageBytes(bytes, directory);
                    }
                    catch { }
                }
            }

            byte[] fileContents = GetStreamBytes(data.GetData("FileContents", false));
            string fromContents = SaveImageBytes(fileContents, directory);
            if (fromContents != null)
                return fromContents;

            string url = ExtractUrl(data, html, fileContents);
            if (url == null)
                return null;
            try
            {
                Uri uri;
                if (!Uri.TryCreate(url, UriKind.Absolute, out uri) ||
                    (uri.Scheme != Uri.UriSchemeHttps && uri.Scheme != Uri.UriSchemeHttp))
                    return null;
                using (var client = new WebClient())
                {
                    client.Headers[HttpRequestHeader.UserAgent] = "Mozilla/5.0";
                    return SaveImageBytes(client.DownloadData(uri), directory);
                }
            }
            catch
            {
                return null;
            }
        }

        private static string SaveImageBytes(byte[] bytes, string directory)
        {
            if (bytes == null || bytes.Length == 0)
                return null;
            try
            {
                using (var stream = new MemoryStream(bytes))
                using (var decoded = System.Drawing.Image.FromStream(stream))
                {
                    string path = AvailablePath(Path.Combine(directory, "image_gmail.png"));
                    decoded.Save(path, System.Drawing.Imaging.ImageFormat.Png);
                    return path;
                }
            }
            catch
            {
                return null;
            }
        }

        private static byte[] GetStreamBytes(object value)
        {
            var directBytes = value as byte[];
            if (directBytes != null)
                return directBytes;
            var streams = value as Stream[];
            if (streams != null && streams.Length > 0)
                value = streams[0];
            var objects = value as object[];
            if (objects != null && objects.Length > 0)
                value = objects[0];
            var stream = value as Stream;
            if (stream == null)
                return null;
            long originalPosition = stream.CanSeek ? stream.Position : 0;
            if (stream.CanSeek) stream.Position = 0;
            using (var copy = new MemoryStream())
            {
                stream.CopyTo(copy);
                if (stream.CanSeek) stream.Position = originalPosition;
                return copy.ToArray();
            }
        }

        private static string ExtractUrl(IDataObject data, string html, byte[] contents)
        {
            string[] formats = {
                "UniformResourceLocatorW",
                "UniformResourceLocator",
                "text/x-moz-url"
            };
            foreach (string format in formats)
            {
                object value = data.GetData(format, false);
                string text = value as string;
                if (text == null)
                {
                    byte[] bytes = GetStreamBytes(value);
                    if (bytes != null)
                        text = format.EndsWith("W")
                            ? System.Text.Encoding.Unicode.GetString(bytes)
                            : System.Text.Encoding.UTF8.GetString(bytes);
                }
                string found = FirstHttpUrl(text);
                if (found != null) return found;
            }
            string contentText = contents == null ? null : System.Text.Encoding.UTF8.GetString(contents);
            string contentUrl = FirstHttpUrl(contentText);
            if (contentUrl == null && contents != null)
                contentUrl = FirstHttpUrl(System.Text.Encoding.Unicode.GetString(contents));
            if (contentUrl != null) return contentUrl;
            if (!String.IsNullOrEmpty(html))
            {
                Match source = Regex.Match(
                    html,
                    @"<img[^>]+src\s*=\s*[""'](?<url>https?://[^""']+)",
                    RegexOptions.IgnoreCase
                );
                if (source.Success)
                    return WebUtility.HtmlDecode(source.Groups["url"].Value);
                string htmlUrl = FirstHttpUrl(WebUtility.HtmlDecode(html));
                if (htmlUrl != null)
                    return htmlUrl;
            }
            return null;
        }

        private static string FirstHttpUrl(string text)
        {
            if (String.IsNullOrEmpty(text)) return null;
            text = text.Replace("\0", "");
            Match match = Regex.Match(text, @"https?://[^\s""'<>\0]+", RegexOptions.IgnoreCase);
            return match.Success ? WebUtility.HtmlDecode(match.Value.TrimEnd('\0')) : null;
        }

        private static object GetField(object value, string name)
        {
            if (value == null) return null;
            FieldInfo field = value.GetType().GetField(name, BindingFlags.NonPublic | BindingFlags.Instance);
            return field == null ? null : field.GetValue(value);
        }

        private static string AvailablePath(string path)
        {
            if (!File.Exists(path)) return path;
            string directory = Path.GetDirectoryName(path);
            string stem = Path.GetFileNameWithoutExtension(path);
            string extension = Path.GetExtension(path);
            for (int index = 1; ; index++)
            {
                string candidate = Path.Combine(directory, stem + " (" + index + ")" + extension);
                if (!File.Exists(candidate)) return candidate;
            }
        }
    }
}
