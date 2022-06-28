from PySide6 import QtCore as qtc, QtWidgets as qtw


class SlidingStackedWidget(qtw.QStackedWidget):
    def __init__(self, parent=None):
        super(SlidingStackedWidget, self).__init__(parent)

        self.m_direction = qtc.Qt.Horizontal
        self.m_speed = 500
        self.m_animation_type = qtc.QEasingCurve.OutCubic
        self.m_now = 0
        self.m_next = 0
        self.m_wrap = False
        self.m_pnow = qtc.QPoint(0, 0)
        self.m_active = False

    def setDirection(
            self,
            direction,
    ) -> None:
        self.m_direction = direction

    def setSpeed(
            self,
            speed,
    ) -> None:
        self.m_speed = speed

    def setAnimation(
            self,
            animation_type,
    ) -> None:
        self.m_animation_type = animation_type

    def setWrap(
            self,
            wrap,
    ) -> None:
        self.m_wrap = wrap

    @qtc.Slot()
    def slideInPrevious(self):
        now = self.currentIndex()
        if self.m_wrap or now > 0:
            self.slideInIndex(now - 1)

    @qtc.Slot()
    def slideInNext(self):
        now = self.currentIndex()
        if self.m_wrap or now < (self.count() - 1):
            self.slideInIndex(now + 1)

    def slideInIndex(self, idx):
        if idx > (self.count() - 1):
            idx %= self.count()
        elif idx < 0:
            idx = (idx + self.count()) % self.count()
        self.slideInWidget(self.widget(idx))

    def slideInWidget(
            self,
            new_widget,
    ) -> None:
        if self.m_active:
            return

        self.m_active = True

        _now = self.currentIndex()
        _next = self.indexOf(new_widget)

        if _now == _next:
            self.m_active = False
            return

        offset_x, offset_y = self.frameRect().width(), self.frameRect().height()
        self.widget(_next).setGeometry(self.frameRect())

        if not self.m_direction == qtc.Qt.Horizontal:
            if _now < _next:
                offset_x, offset_y = 0, -offset_y
            else:
                offset_x = 0
        else:
            if _now < _next:
                offset_x, offset_y = -offset_x, 0
            else:
                offset_y = 0

        p_next = self.widget(_next).pos()
        pnow = self.widget(_now).pos()
        self.m_pnow = pnow

        offset = qtc.QPoint(offset_x, offset_y)
        self.widget(_next).move(p_next - offset)
        self.widget(_next).show()
        self.widget(_next).raise_()

        anim_group = qtc.QParallelAnimationGroup(
            self,
            finished=self.animationDoneSlot,  # noqa
        )

        for index, start, end in zip(
            (_now, _next), (pnow, p_next - offset), (pnow + offset, p_next)
        ):
            animation = qtc.QPropertyAnimation(  # noqa
                self.widget(index),
                b"pos",
                duration=self.m_speed,
                easingCurve=self.m_animation_type,
                startValue=start,
                endValue=end,
            )
            anim_group.addAnimation(animation)

        self.m_next = _next
        self.m_now = _now
        self.m_active = True
        anim_group.start(qtc.QAbstractAnimation.DeleteWhenStopped)

    @qtc.Slot()
    def animationDoneSlot(self):
        self.setCurrentIndex(self.m_next)
        self.widget(self.m_now).hide()
        self.widget(self.m_now).move(self.m_pnow)
        self.m_active = False
