package online.slickk.shand

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(28, 40, 28, 28)
        }
        val status = TextView(this).apply { text = "S-Hand Android: local action test" }
        val field = EditText(this).apply { hint = "Focus this field to test typing" }
        val settings = Button(this).apply {
            text = "Enable Accessibility Service"
            setOnClickListener { startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) }
        }
        val type = Button(this).apply {
            text = "Test real typing"
            setOnClickListener {
                field.requestFocus()
                val ok = HandAccessibilityService.instance?.typeText("Hello from S-Hand") ?: false
                status.text = if (ok) "Typing action accepted" else "Enable service and focus editable field"
            }
        }
        val back = Button(this).apply {
            text = "Test Back action"
            setOnClickListener {
                status.text = if (HandAccessibilityService.instance?.navigateBack() == true)
                    "Back action accepted" else "Accessibility service unavailable"
            }
        }
        listOf(status, field, settings, type, back).forEach { layout.addView(it) }
        setContentView(layout)
    }
}
