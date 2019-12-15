# flask_dashboard

starting redis:

```
redis-server redis.conf
```




    <div class="sidebar-heading">X values:</div>
    <div class="input-group margin-bottom-sm" style="padding-right: 15px; padding-left: 15px;" >
        <select name=xcols method="GET" action="/">
            {% for xcol in xcols %}
                {% if {{xvals}} == {{xcol}} %}
                    <option value={{xcol}} SELECTED>{{xcol}}</option>"
                {% else %}
                    <option value={{xcol}}>{{xcol}}</option>"
                {% endif %}
            {% endfor %}
        </select>
    </div>

    <!-- Divider -->
    <hr class="sidebar-divider d-none d-md-block">

    <div class="sidebar-heading">Y values:</div>
    <div class="input-group margin-bottom-sm" style="padding-right: 15px; padding-left: 15px;" >
        <select name=ycols method="GET" action="/">
            {% for ycol in ycols %}
                {% if {{yvals}} == {{ycol}} %}
                    <option value={{ycol}} SELECTED>{{ycol}}</option>"
                {% else %}
                    <option value={{ycol}}>{{ycol}}</option>"
                {% endif %}                
            {% endfor %}
        </select>
    </div>