# DataTables 2.0+ with Bootstrap 5 Styling Guide

## 1. Installation & Setup

### CSS includes (in `<head>`)
```html
<!-- Bootstrap 5 CSS -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<!-- DataTables CSS -->
<link href="https://cdn.jsdelivr.net/npm/datatables@2.0.0/css/dataTables.bootstrap5.css" rel="stylesheet">

<!-- Optional: DataTables Extensions -->
<link href="https://cdn.jsdelivr.net/npm/datatables-buttons@2.4.1/css/buttons.bootstrap5.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/datatables-select@1.7.0/css/select.bootstrap5.css" rel="stylesheet">
```

### JavaScript includes (before closing `</body>`)
```html
<!-- Bootstrap JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<!-- jQuery (required by DataTables) -->
<script src="https://code.jquery.com/jquery-3.7.0.js"></script>

<!-- DataTables JS -->
<script src="https://cdn.jsdelivr.net/npm/datatables@2.0.0/js/dataTables.js"></script>
<script src="https://cdn.jsdelivr.net/npm/datatables@2.0.0/js/dataTables.bootstrap5.js"></script>

<!-- Optional: Extensions -->
<script src="https://cdn.jsdelivr.net/npm/datatables-buttons@2.4.1/js/dataTables.buttons.js"></script>
<script src="https://cdn.jsdelivr.net/npm/datatables-buttons@2.4.1/js/buttons.bootstrap5.js"></script>
```

## 2. Basic HTML Structure

```html
<table id="example" class="table table-striped">
  <thead>
    <tr>
      <th>Name</th>
      <th>Email</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>John Doe</td>
      <td>john@example.com</td>
      <td>Active</td>
    </tr>
  </tbody>
</table>
```

## 3. Basic Initialization

```javascript
new DataTable('#example', {
  responsive: true,
  pageLength: 25,
  ordering: true,
  searching: true,
  paging: true,
  info: true,
  layout: {
    topStart: 'pageLength',
    topEnd: 'search',
    bottomStart: 'info',
    bottomEnd: 'paging'
  }
});
```

## 4. Common Customizations

### 4.1 Search & Filter Box Styling

```javascript
new DataTable('#example', {
  layout: {
    topStart: 'pageLength',
    topEnd: 'search',
    bottomStart: 'info',
    bottomEnd: 'paging'
  }
});
```

The `layout` option automatically handles Bootstrap 5 grid integration. Control elements are placed in their positions and styled consistently with Bootstrap.

### 4.2 Column Visibility Toggle
```javascript
new DataTable('#example', {
  columnDefs: [
    {
      targets: 0,
      visible: true,
      responsivePriority: 1
    },
    {
      targets: 1,
      visible: true,
      responsivePriority: 2
    }
  ],
  layout: {
    topStart: 'pageLength',
    topEnd: 'search',
    bottomStart: 'info',
    bottomEnd: 'paging'
  }
});
```

### 4.3 Button Integration (with Buttons extension)
```javascript
new DataTable('#example', {
  layout: {
    topStart: {
      buttons: [
        {
          extend: 'copy',
          className: 'btn btn-sm btn-outline-secondary'
        },
        {
          extend: 'csv',
          className: 'btn btn-sm btn-outline-secondary'
        },
        {
          extend: 'excel',
          className: 'btn btn-sm btn-outline-secondary'
        },
        {
          extend: 'pdf',
          className: 'btn btn-sm btn-outline-secondary'
        },
        {
          extend: 'print',
          className: 'btn btn-sm btn-outline-secondary'
        }
      ]
    },
    topEnd: 'search',
    bottomStart: 'info',
    bottomEnd: 'paging'
  }
});
```

## 5. Advanced Styling

### 5.1 Custom Row Coloring
```javascript
new DataTable('#example', {
  createdRow: function(row, data, dataIndex) {
    if (data[2] === 'Inactive') {
      $(row).addClass('table-danger');
    }
  },
  layout: {
    topStart: 'pageLength',
    topEnd: 'search',
    bottomStart: 'info',
    bottomEnd: 'paging'
  }
});
```

### 5.2 Bootstrap 5 Utility Classes
```html
<!-- Add Bootstrap classes directly to the table -->
<table id="example" class="table table-striped table-hover table-sm">
```

Options:
- `table-striped` - Alternate row colors
- `table-hover` - Highlight on row hover
- `table-sm` - Compact table
- `table-bordered` - Add borders
- `table-borderless` - Remove borders

### 5.3 Responsive Breakpoints
```javascript
new DataTable('#example', {
  responsive: {
    details: {
      display: $.fn.dataTable.Responsive.display.modal({
        header: function(row) {
          return 'Details: ' + row.data()[0];
        }
      }),
      renderer: $.fn.dataTable.Responsive.renderer.tableAll()
    }
  },
  layout: {
    topStart: 'pageLength',
    topEnd: 'search',
    bottomStart: 'info',
    bottomEnd: 'paging'
  }
});
```

## 6. CSS Customization

### 6.1 Override Default Styles
```css
/* Custom styling for DataTables with Bootstrap 5 */

.dataTables_wrapper {
  margin-top: 20px;
}

.dataTables_filter input,
.dataTables_length select {
  padding: 0.375rem 0.75rem;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
}

.dt-paging {
  margin-top: 1rem;
}

/* Style pagination with Bootstrap classes */
.dt-paging .dt-paging-button {
  padding: 0.375rem 0.75rem;
  border: 1px solid #dee2e6;
}

.dt-paging .dt-paging-button.active {
  background-color: #0d6efd;
  color: white;
}
```

### 6.2 Theme Integration
```css
/* Light theme (Bootstrap default) */
.dataTables_wrapper .table {
  color: #212529;
}

/* Dark theme */
.dark-theme .dataTables_wrapper .table {
  color: #f8f9fa;
  background-color: #212529;
}

.dark-theme .dataTables_filter input,
.dark-theme .dataTables_length select {
  background-color: #343a40;
  color: #f8f9fa;
  border-color: #495057;
}
```

## 7. Layout Position Reference

The `layout` option uses directional keys for positioning:

| Position | Description |
|----------|-------------|
| `topStart` | Top-left (or top-start in RTL) |
| `topEnd` | Top-right (or top-end in RTL) |
| `bottomStart` | Bottom-left (or bottom-start in RTL) |
| `bottomEnd` | Bottom-right (or bottom-end in RTL) |

You can also specify multiple rows:
- `top1Start`, `top1End` (first row)
- `top2Start`, `top2End` (second row)
- Similar for bottom rows

## 8. Multi-Row Layout Example

```javascript
new DataTable('#example', {
  layout: {
    top1Start: {
      buttons: ['copy', 'csv', 'excel']
    },
    top1End: 'search',
    top2Start: 'pageLength',
    top2End: 'info',
    bottom: 'paging'
  }
});
```

## 9. Complete Example

```html
<!DOCTYPE html>
<html>
<head>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/datatables@2.0.0/css/dataTables.bootstrap5.css" rel="stylesheet">
</head>
<body>
<div class="container-fluid mt-5">
  <h1>Users</h1>
  <table id="users" class="table table-striped">
    <thead>
      <tr>
        <th>Name</th>
        <th>Email</th>
        <th>Role</th>
        <th>Joined</th>
      </tr>
    </thead>
    <tbody>
      <!-- Data rows -->
    </tbody>
  </table>
</div>

<script src="https://code.jquery.com/jquery-3.7.0.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/datatables@2.0.0/js/dataTables.js"></script>
<script src="https://cdn.jsdelivr.net/npm/datatables@2.0.0/js/dataTables.bootstrap5.js"></script>

<script>
new DataTable('#users', {
  responsive: true,
  pageLength: 25,
  layout: {
    topStart: 'pageLength',
    topEnd: 'search',
    bottomStart: 'info',
    bottomEnd: 'paging'
  }
});
</script>
</body>
</html>
```

## 10. Key Bootstrap 5 Integration Points

| Feature | Bootstrap Class | DataTables Config |
|---------|-----------------|-------------------|
| Responsive | `.table-responsive` | `responsive: true` |
| Striped rows | `.table-striped` | CSS class on table |
| Hover effect | `.table-hover` | CSS class on table |
| Small table | `.table-sm` | CSS class on table |
| Colors | `.table-danger`, `.table-success` | `createdRow` callback |

## 11. Best Practices

1. **Use `layout` instead of deprecated `dom` option**
2. **Always include Bootstrap 5 CSS before DataTables Bootstrap5 CSS**
3. **Use responsive mode for mobile compatibility**
4. **Minimize DOM manipulation in callbacks for performance**
5. **Test across browsers and devices**
6. **Leverage Bootstrap utility classes for consistency**
7. **Use `topStart`, `topEnd`, `bottomStart`, `bottomEnd` for intuitive positioning**

## Notes

- `layout` is the modern approach introduced in DataTables 2.0.0
- The deprecated `dom` option should not be used for new projects
- The `layout` option is more flexible and styling framework independent
- RTL (right-to-left) is better supported with `Start`/`End` positioning
