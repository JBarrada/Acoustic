from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from ctypes import sizeof, memmove, addressof, create_string_buffer
import colorsys
import numpy
import math
import analyze


class Texture:
    def __init__(self):
        empty = 0

    @staticmethod
    def upload_texture(width, height, bitmap):
        tex_buf = glGenBuffers(1)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, tex_buf)
        glBufferData(GL_PIXEL_UNPACK_BUFFER, width*height, None, GL_STREAM_DRAW)
        datapointer = glMapBuffer(GL_PIXEL_UNPACK_BUFFER, GL_WRITE_ONLY)
        memmove(datapointer, addressof(bitmap), width*height)
        glUnmapBuffer(GL_PIXEL_UNPACK_BUFFER)

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, tex_buf)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_ALPHA, width, height, 0, GL_ALPHA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glDeleteBuffers(1, [tex_buf])
        return tex_id

    @staticmethod
    def update_texture(width, height, bitmap, tex_id):
        tex_buf = glGenBuffers(1)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, tex_buf)
        glBufferData(GL_PIXEL_UNPACK_BUFFER, width*height, None, GL_STREAM_DRAW)
        datapointer = glMapBuffer(GL_PIXEL_UNPACK_BUFFER, GL_WRITE_ONLY)
        memmove(datapointer, addressof(bitmap), width*height)
        glUnmapBuffer(GL_PIXEL_UNPACK_BUFFER)

        glBindTexture(GL_TEXTURE_2D, tex_id)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, tex_buf)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_ALPHA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glDeleteBuffers(1, [tex_buf])

    @staticmethod
    def draw_texture_block(bottom, s_height, tex_width, offset, tex_offset, tex_id):
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glBegin(GL_QUADS)
        glTexCoord2i(0, 0)
        glVertex2f(offset+tex_offset, bottom)
        glTexCoord2i(1, 0)
        glVertex2f(offset+tex_offset+tex_width, bottom)
        glTexCoord2i(1, 1)
        glVertex2f(offset+tex_offset+tex_width, bottom+s_height)
        glTexCoord2i(0, 1)
        glVertex2f(offset+tex_offset, bottom+s_height)
        glEnd()


class WaveformDisplay:
    def __init__(self, data):
        self.tex_ids = []
        self.data = data

    def draw(self, offset, scale, w_width, w_height, r, g, b, a=1.0):
        t_width = len(self.data)
        glEnable(GL_TEXTURE_2D)
        glColor4f(r, g, b, a)

        tex_id_n = 0
        for block in range(0, t_width, 256):
            b_width = 256 if block+256 <= t_width else (t_width-block)
            b_width = (4-(b_width % 4))+b_width if b_width % 4 != 0 else b_width

            tex_offset = (float(block)/t_width)*(w_width*scale)
            tex_width = (float(b_width)/t_width)*(w_width*scale)

            if 0-tex_width < offset+tex_offset < w_width:
                Texture.draw_texture_block(0, w_height, tex_width, offset, tex_offset, self.tex_ids[tex_id_n])

            tex_id_n += 1

        glDisable(GL_TEXTURE_2D)

    def create_tex(self):
        t_width, t_height = len(self.data), 256
        for block in range(0, t_width-1, 256):
            b_width = 256 if block+256 <= t_width else (t_width-block)
            b_width_a = (4-(b_width % 4))+b_width if b_width % 4 != 0 else b_width
            bitmap = self.bitmap_gen(block, b_width_a, b_width, t_height)
            tex_id = Texture.upload_texture(b_width_a, t_height, bitmap)
            self.tex_ids += [tex_id]

    def bitmap_gen(self, block, width_a, width, height):
        bitmap = create_string_buffer(height*width_a)

        for s in range(block, block+width):
            normalized = ((self.data[s] / 65535.0) + 0.5) * height
            bitmap[int(normalized)*width_a+(s-block)] = chr(255)

            if s > 0:
                last_norm = ((self.data[s-1] / 65535.0) + 0.5) * height

                dist = int((normalized - last_norm) / 2)
                start = int(min(normalized+1, normalized - dist))

                for i in range(start, start+abs(dist)):
                    bitmap[int(i)*width_a+(s-block)] = chr(100)

            if s < (len(self.data)-1):
                next_norm = ((self.data[s+1] / 65535.0) + 0.5) * height

                dist = int((normalized - next_norm) / 2)
                start = int(min(normalized+1, normalized - dist))

                for i in range(start, start+abs(dist)):
                    bitmap[int(i)*width_a+(s-block)] = chr(100)

        return bitmap


class Marker:
    def __init__(self, pos, color):
        self.pos = pos
        self.color = color


class Display:
    W_WIDTH = 600
    W_HEIGHT = 100

    scale = 1.0
    offset = 0
    view_grab = False
    view_grab_x = 0
    offset_temp = 0

    def __init__(self, width, height, wave_display, sample_rate):
        self.W_WIDTH = width
        self.W_HEIGHT = height
        self.wave_display = wave_display
        self.sample_rate = sample_rate
        self.marker_pos_a = 0
        self.marker_pos_b = 0
        self.markers = []

    def init(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(2.0)
        glPointSize(5.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0.0, self.W_WIDTH, 0.0, self.W_HEIGHT)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.wave_display.create_tex()

    def start_window(self):
        glutInit()

        glutInitWindowSize(self.W_WIDTH, self.W_HEIGHT)
        glutCreateWindow("!!!")
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
        # glutCloseFunc(self.close)
        glutDisplayFunc(self.display)
        glutKeyboardFunc(self.keyboard)
        glutMouseWheelFunc(self.mouse_wheel)
        glutMouseFunc(self.mouse)
        glutMotionFunc(self.motion)
        glutIdleFunc(self.idle)

        self.init()

        glutMainLoop()

    def keyboard(self, key, x, y):
        placeholder = self.scale

    def motion(self, x, y):
        if self.view_grab:
            self.offset = self.offset_temp - (self.view_grab_x-x)
            self.offset = 0 if self.offset > 0 else self.offset

    def marker_info(self):
        marker_a_ms = (self.marker_pos_a / float(self.sample_rate)) * 1000.0
        marker_b_ms = (self.marker_pos_b / float(self.sample_rate)) * 1000.0

        delta_samples = math.fabs(self.marker_pos_a - self.marker_pos_b)
        delta_ms = (delta_samples / float(self.sample_rate)) * 1000.0

        print("A: %d (%0.3fmS)" % (self.marker_pos_a, marker_a_ms))
        print("B: %d (%0.3fmS)" % (self.marker_pos_b, marker_b_ms))
        print("DELTA: %d (%0.3fmS)" % (delta_samples, delta_ms))

        if delta_samples < 50000:
            self.markers = analyze.analyze(self.wave_display.data, min(self.marker_pos_a, self.marker_pos_b),
                                 max(self.marker_pos_a, self.marker_pos_b))

    def mouse(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON:
            if state == GLUT_DOWN:
                pos = (-self.offset+((float(x)/glutGet(GLUT_WINDOW_WIDTH))*self.W_WIDTH))/(self.W_WIDTH*self.scale)
                self.marker_pos_a = int(pos*len(self.wave_display.data))
                self.marker_info()

        if button == GLUT_RIGHT_BUTTON:
            if state == GLUT_DOWN:
                pos = (-self.offset+((float(x)/glutGet(GLUT_WINDOW_WIDTH))*self.W_WIDTH))/(self.W_WIDTH*self.scale)
                self.marker_pos_b = int(pos*len(self.wave_display.data))
                self.marker_info()

        if button == GLUT_MIDDLE_BUTTON:
            if state == GLUT_DOWN:
                self.view_grab = True
                self.view_grab_x = x
                self.offset_temp = self.offset
            else:
                self.view_grab = False

    def mouse_wheel(self, wheel, direction, x, y):
        x = (float(x)/glutGet(GLUT_WINDOW_WIDTH))*self.W_WIDTH
        p_scale = self.scale
        self.scale *= (1.0+(direction/5.0))
        self.scale = numpy.clip(self.scale, 1.0, 1000.0)
        i_scale = self.scale/p_scale

        self.offset -= ((x-self.offset)*i_scale)-(x-self.offset)
        self.offset = 0 if self.offset > 0 else self.offset

    def draw_marker(self, marker):
        markerx = self.offset+(float(marker.pos)/len(self.wave_display.data))*(self.W_WIDTH*self.scale)
        glColor3f(marker.color[0], marker.color[1], marker.color[2])
        glVertex2f(markerx, (marker.height / 32768.0) * (self.W_HEIGHT / 2.0) + (self.W_HEIGHT / 2.0))

    def display(self):
        glClear(GL_COLOR_BUFFER_BIT)

        self.wave_display.draw(self.offset, self.scale, self.W_WIDTH, self.W_HEIGHT, 1, 1, 1)

        glBegin(GL_POINTS)
        for marker in self.markers:
            self.draw_marker(marker)
        glEnd()

        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        markerx_a = self.offset+(float(self.marker_pos_a)/len(self.wave_display.data))*(self.W_WIDTH*self.scale)
        glVertex2f(markerx_a, 0)
        glVertex2f(markerx_a, self.W_HEIGHT)
        glEnd()

        glColor3f(0.0, 0.0, 1.0)
        glBegin(GL_LINES)
        markerx_b = self.offset+(float(self.marker_pos_b)/len(self.wave_display.data))*(self.W_WIDTH*self.scale)
        glVertex2f(markerx_b, 0)
        glVertex2f(markerx_b, self.W_HEIGHT)
        glEnd()

        glFlush()

    def idle(self):
        self.display()
